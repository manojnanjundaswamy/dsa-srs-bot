import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from task_engine.database import get_db
from task_engine.models import Asset, AssetRecord, User, UserRecord, UserMeta
from task_engine.schemas import (
    RecordWithState, ReviewRequest, ReviewResponse,
    UserCreate, UserMetaResponse, UserRecordResponse,
    UserRecordStateUpdate, UserResponse, UserStatsResponse, UserUpdate,
)
from task_engine.asset_helpers import (
    apply_review, get_due_records, get_next_record,
    get_user_stats, _update_user_meta,
)

router = APIRouter(prefix="/api/users", tags=["users"])


def _get_user_or_404(user_id: str, db: Session) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    return user


def _get_asset_or_404(asset_id: str, db: Session) -> Asset:
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")
    return asset


# ── User CRUD ─────────────────────────────────────────────────────────────────

@router.get("", response_model=List[UserResponse])
def list_users(db: Session = Depends(get_db)):
    return db.query(User).order_by(User.created_at).all()


@router.post("", response_model=UserResponse, status_code=201)
def create_user(body: UserCreate, db: Session = Depends(get_db)):
    user = User(
        id=str(uuid.uuid4()),
        name=body.name,
        telegram_chat_id=body.telegram_chat_id,
        metadata_=body.metadata_,
        enabled=body.enabled,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: str, db: Session = Depends(get_db)):
    return _get_user_or_404(user_id, db)


@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: str, body: UserUpdate, db: Session = Depends(get_db)):
    user = _get_user_or_404(user_id, db)
    updates = body.model_dump(exclude_none=True)
    if "metadata_" in updates:
        user.metadata_ = updates.pop("metadata_")
    for field, value in updates.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


# ── UserRecord (progress/state) endpoints ────────────────────────────────────

@router.get("/{user_id}/assets/{asset_id}/records", response_model=List[RecordWithState])
def list_user_records(
    user_id: str,
    asset_id: str,
    status: Optional[str] = None,
    limit: int = Query(default=50, le=500),
    offset: int = Query(default=0),
    db: Session = Depends(get_db),
):
    """All AssetRecords for this asset, merged with the user's state."""
    _get_user_or_404(user_id, db)
    _get_asset_or_404(asset_id, db)

    records = (
        db.query(AssetRecord)
        .filter(AssetRecord.asset_id == asset_id)
        .order_by(AssetRecord.order)
        .offset(offset)
        .limit(limit)
        .all()
    )
    user_state_map = {
        ur.record_key: ur.state
        for ur in db.query(UserRecord).filter(
            UserRecord.user_id == user_id,
            UserRecord.asset_id == asset_id,
        ).all()
    }

    result = []
    for rec in records:
        state = user_state_map.get(rec.record_key)
        if status and (not state or state.get("status") != status):
            continue
        result.append(RecordWithState(
            record_key=rec.record_key,
            data=rec.data,
            order=rec.order,
            state=state,
        ))
    return result


@router.get("/{user_id}/assets/{asset_id}/records/{record_key}", response_model=RecordWithState)
def get_user_record(user_id: str, asset_id: str, record_key: str,
                    db: Session = Depends(get_db)):
    rec = db.query(AssetRecord).filter(
        AssetRecord.asset_id == asset_id,
        AssetRecord.record_key == record_key,
    ).first()
    if not rec:
        raise HTTPException(status_code=404, detail=f"Record '{record_key}' not found")

    ur = db.query(UserRecord).filter(
        UserRecord.user_id == user_id,
        UserRecord.asset_id == asset_id,
        UserRecord.record_key == record_key,
    ).first()

    return RecordWithState(record_key=rec.record_key, data=rec.data,
                           order=rec.order, state=ur.state if ur else None)


@router.put("/{user_id}/assets/{asset_id}/records/{record_key}/state",
            response_model=UserRecordResponse)
def update_user_record_state(user_id: str, asset_id: str, record_key: str,
                              body: UserRecordStateUpdate, db: Session = Depends(get_db)):
    """Partial merge of state into the user's record."""
    _get_user_or_404(user_id, db)

    ur = db.query(UserRecord).filter(
        UserRecord.user_id == user_id,
        UserRecord.asset_id == asset_id,
        UserRecord.record_key == record_key,
    ).first()

    if not ur:
        ur = UserRecord(
            id=str(uuid.uuid4()),
            user_id=user_id,
            asset_id=asset_id,
            record_key=record_key,
            state={},
        )
        db.add(ur)

    merged = dict(ur.state or {})
    merged.update(body.state)
    ur.state = merged
    ur.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(ur)
    return ur


@router.post("/{user_id}/assets/{asset_id}/records/{record_key}/review",
             response_model=ReviewResponse)
def review_record(user_id: str, asset_id: str, record_key: str,
                  body: ReviewRequest, db: Session = Depends(get_db)):
    """Apply SM-2 spaced repetition update for a reviewed record."""
    _get_user_or_404(user_id, db)
    if body.difficulty not in ("easy", "medium", "hard"):
        raise HTTPException(status_code=400, detail="difficulty must be easy, medium, or hard")

    ur = apply_review(user_id, asset_id, record_key, body.difficulty, db)
    return ReviewResponse(
        record_key=record_key,
        new_state=ur.state,
        next_due=ur.state.get("next_due"),
    )


@router.get("/{user_id}/assets/{asset_id}/next", response_model=Optional[RecordWithState])
def next_record(user_id: str, asset_id: str, db: Session = Depends(get_db)):
    """Return the next unstarted record for this user in the asset."""
    _get_user_or_404(user_id, db)
    result = get_next_record(user_id, asset_id, db)
    if not result:
        return None
    rec, ur = result
    return RecordWithState(record_key=rec.record_key, data=rec.data,
                           order=rec.order, state=ur.state if ur else None)


@router.get("/{user_id}/assets/{asset_id}/due", response_model=List[RecordWithState])
def due_records(user_id: str, asset_id: str, db: Session = Depends(get_db)):
    """Return all records due for review today (SM-2 scheduled)."""
    _get_user_or_404(user_id, db)
    pairs = get_due_records(user_id, asset_id, db)
    return [
        RecordWithState(record_key=rec.record_key, data=rec.data,
                        order=rec.order, state=ur.state)
        for rec, ur in pairs
    ]


@router.get("/{user_id}/assets/{asset_id}/stats", response_model=UserStatsResponse)
def user_stats(user_id: str, asset_id: str, db: Session = Depends(get_db)):
    """Aggregate progress stats: streak, solved count, weak patterns."""
    _get_user_or_404(user_id, db)
    _get_asset_or_404(asset_id, db)
    stats = get_user_stats(user_id, asset_id, db)
    return UserStatsResponse(**stats)
