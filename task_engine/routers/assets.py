import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from task_engine.database import get_db
from task_engine.models import Asset, AssetRecord, Task, TaskAsset
from task_engine.schemas import (
    AssetCreate, AssetRecordCreate, AssetRecordResponse, AssetRecordUpdate,
    AssetResponse, AssetUpdate, TaskAssetLink, TaskAssetResponse,
)

router = APIRouter(prefix="/api", tags=["assets"])


def _get_asset_or_404(asset_id: str, db: Session) -> Asset:
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")
    return asset


# ── Asset CRUD ────────────────────────────────────────────────────────────────

@router.get("/assets", response_model=List[AssetResponse])
def list_assets(db: Session = Depends(get_db)):
    return db.query(Asset).order_by(Asset.created_at).all()


@router.post("/assets", response_model=AssetResponse, status_code=201)
def create_asset(body: AssetCreate, db: Session = Depends(get_db)):
    asset = Asset(
        id=str(uuid.uuid4()),
        name=body.name,
        type=body.type,
        description=body.description,
        record_schema=body.record_schema,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


@router.get("/assets/{asset_id}", response_model=AssetResponse)
def get_asset(asset_id: str, db: Session = Depends(get_db)):
    return _get_asset_or_404(asset_id, db)


@router.put("/assets/{asset_id}", response_model=AssetResponse)
def update_asset(asset_id: str, body: AssetUpdate, db: Session = Depends(get_db)):
    asset = _get_asset_or_404(asset_id, db)
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(asset, field, value)
    db.commit()
    db.refresh(asset)
    return asset


@router.delete("/assets/{asset_id}", status_code=204)
def delete_asset(asset_id: str, db: Session = Depends(get_db)):
    asset = _get_asset_or_404(asset_id, db)
    db.delete(asset)
    db.commit()


# ── AssetRecord CRUD ──────────────────────────────────────────────────────────

@router.get("/assets/{asset_id}/records", response_model=List[AssetRecordResponse])
def list_records(
    asset_id: str,
    limit: int = Query(default=50, le=500),
    offset: int = Query(default=0),
    db: Session = Depends(get_db),
):
    _get_asset_or_404(asset_id, db)
    return (
        db.query(AssetRecord)
        .filter(AssetRecord.asset_id == asset_id)
        .order_by(AssetRecord.order)
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.post("/assets/{asset_id}/records", response_model=AssetRecordResponse, status_code=201)
def create_record(asset_id: str, body: AssetRecordCreate, db: Session = Depends(get_db)):
    _get_asset_or_404(asset_id, db)
    existing = db.query(AssetRecord).filter(
        AssetRecord.asset_id == asset_id,
        AssetRecord.record_key == body.record_key,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Record key '{body.record_key}' already exists in this asset")

    rec = AssetRecord(
        id=str(uuid.uuid4()),
        asset_id=asset_id,
        record_key=body.record_key,
        data=body.data,
        order=body.order,
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec


@router.get("/assets/{asset_id}/records/{record_key}", response_model=AssetRecordResponse)
def get_record(asset_id: str, record_key: str, db: Session = Depends(get_db)):
    rec = db.query(AssetRecord).filter(
        AssetRecord.asset_id == asset_id,
        AssetRecord.record_key == record_key,
    ).first()
    if not rec:
        raise HTTPException(status_code=404, detail=f"Record '{record_key}' not found in asset {asset_id}")
    return rec


@router.put("/assets/{asset_id}/records/{record_key}", response_model=AssetRecordResponse)
def update_record(asset_id: str, record_key: str, body: AssetRecordUpdate,
                  db: Session = Depends(get_db)):
    rec = db.query(AssetRecord).filter(
        AssetRecord.asset_id == asset_id,
        AssetRecord.record_key == record_key,
    ).first()
    if not rec:
        raise HTTPException(status_code=404, detail=f"Record '{record_key}' not found")
    if body.data is not None:
        rec.data = body.data
    if body.order is not None:
        rec.order = body.order
    db.commit()
    db.refresh(rec)
    return rec


@router.delete("/assets/{asset_id}/records/{record_key}", status_code=204)
def delete_record(asset_id: str, record_key: str, db: Session = Depends(get_db)):
    rec = db.query(AssetRecord).filter(
        AssetRecord.asset_id == asset_id,
        AssetRecord.record_key == record_key,
    ).first()
    if not rec:
        raise HTTPException(status_code=404, detail=f"Record '{record_key}' not found")
    db.delete(rec)
    db.commit()


# ── Task-Asset linkage ────────────────────────────────────────────────────────

@router.get("/tasks/{task_id}/assets", response_model=List[TaskAssetResponse])
def list_task_assets(task_id: str, db: Session = Depends(get_db)):
    links = db.query(TaskAsset).filter(TaskAsset.task_id == task_id).all()
    result = []
    for link in links:
        asset = db.query(Asset).filter(Asset.id == link.asset_id).first()
        result.append(TaskAssetResponse(
            task_id=link.task_id,
            asset_id=link.asset_id,
            role=link.role,
            asset_name=asset.name if asset else None,
        ))
    return result


@router.post("/tasks/{task_id}/assets", response_model=TaskAssetResponse, status_code=201)
def link_task_asset(task_id: str, body: TaskAssetLink, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    _get_asset_or_404(body.asset_id, db)

    existing = db.query(TaskAsset).filter(
        TaskAsset.task_id == task_id,
        TaskAsset.asset_id == body.asset_id,
    ).first()
    if existing:
        existing.role = body.role
        db.commit()
        db.refresh(existing)
        link = existing
    else:
        link = TaskAsset(task_id=task_id, asset_id=body.asset_id, role=body.role)
        db.add(link)
        db.commit()

    asset = db.query(Asset).filter(Asset.id == body.asset_id).first()
    return TaskAssetResponse(task_id=task_id, asset_id=body.asset_id,
                             role=body.role, asset_name=asset.name if asset else None)


@router.delete("/tasks/{task_id}/assets/{asset_id}", status_code=204)
def unlink_task_asset(task_id: str, asset_id: str, db: Session = Depends(get_db)):
    link = db.query(TaskAsset).filter(
        TaskAsset.task_id == task_id,
        TaskAsset.asset_id == asset_id,
    ).first()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    db.delete(link)
    db.commit()
