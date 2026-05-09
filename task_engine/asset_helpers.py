"""
DB-native helper functions for the asset/user/record data layer.

These are injected into the task executor context so scripts can call them
without imports. All functions that need a DB session accept it as a kwarg
so they can be partially applied at inject time.
"""

from datetime import datetime, timedelta, date
from functools import partial
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from task_engine.models import Asset, AssetRecord, User, UserRecord, UserMeta, Interaction


# ── User helpers ──────────────────────────────────────────────────────────────

def get_user(telegram_chat_id: str, db: Session) -> Optional[User]:
    """Return a User row by Telegram chat ID, or None."""
    return db.query(User).filter(User.telegram_chat_id == telegram_chat_id).first()


def get_user_by_id(user_id: str, db: Session) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def get_or_create_user(telegram_chat_id: str, name: str, db: Session) -> User:
    user = get_user(telegram_chat_id, db)
    if not user:
        from task_engine.models import _uuid
        user = User(id=_uuid(), name=name, telegram_chat_id=telegram_chat_id)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


# ── Asset helpers ─────────────────────────────────────────────────────────────

def get_asset(name_or_id: str, db: Session) -> Optional[Asset]:
    """Look up an asset by ID or name."""
    asset = db.query(Asset).filter(Asset.id == name_or_id).first()
    if not asset:
        asset = db.query(Asset).filter(Asset.name == name_or_id).first()
    return asset


def list_asset_records(asset_id: str, db: Session) -> List[AssetRecord]:
    return db.query(AssetRecord).filter(
        AssetRecord.asset_id == asset_id
    ).order_by(AssetRecord.order).all()


# ── UserRecord helpers ────────────────────────────────────────────────────────

def get_record_state(user_id: str, asset_id: str, record_key: str, db: Session) -> Optional[UserRecord]:
    return db.query(UserRecord).filter(
        UserRecord.user_id == user_id,
        UserRecord.asset_id == asset_id,
        UserRecord.record_key == record_key,
    ).first()


def get_or_create_record_state(user_id: str, asset_id: str, record_key: str,
                                default_state: dict, db: Session) -> UserRecord:
    ur = get_record_state(user_id, asset_id, record_key, db)
    if not ur:
        from task_engine.models import _uuid
        ur = UserRecord(
            id=_uuid(),
            user_id=user_id,
            asset_id=asset_id,
            record_key=record_key,
            state=default_state,
        )
        db.add(ur)
        db.commit()
        db.refresh(ur)
    return ur


def get_next_record(user_id: str, asset_id: str,
                    db: Session) -> Optional[Tuple[AssetRecord, Optional[UserRecord]]]:
    """
    Return the next AssetRecord this user hasn't started yet (status='new' or no UserRecord).
    Falls back to returning the first record with status='new' if all have been touched.
    """
    records = list_asset_records(asset_id, db)
    started_keys = {
        ur.record_key for ur in db.query(UserRecord).filter(
            UserRecord.user_id == user_id,
            UserRecord.asset_id == asset_id,
        ).all()
    }

    for rec in records:
        ur = None
        if rec.record_key in started_keys:
            ur = get_record_state(user_id, asset_id, rec.record_key, db)
            if ur and ur.state.get("status") != "new":
                continue
        return (rec, ur)

    return None


def get_due_records(user_id: str, asset_id: str,
                    db: Session) -> List[Tuple[AssetRecord, UserRecord]]:
    """
    Return records whose next_due is today or earlier AND status is 'active'.
    """
    today_str = date.today().isoformat()

    due_user_records = db.query(UserRecord).filter(
        UserRecord.user_id == user_id,
        UserRecord.asset_id == asset_id,
    ).all()

    result = []
    for ur in due_user_records:
        state = ur.state or {}
        if state.get("status") != "active":
            continue
        next_due = state.get("next_due", "")
        if next_due and next_due <= today_str:
            rec = db.query(AssetRecord).filter(
                AssetRecord.asset_id == asset_id,
                AssetRecord.record_key == ur.record_key,
            ).first()
            if rec:
                result.append((rec, ur))

    result.sort(key=lambda t: t[1].state.get("next_due", ""))
    return result


# ── SM-2 algorithm ────────────────────────────────────────────────────────────

def apply_review(user_id: str, asset_id: str, record_key: str,
                 difficulty: str, db: Session) -> UserRecord:
    """
    Apply SM-2 spaced repetition update for a record review.
    difficulty: "easy" | "medium" | "hard"
    """
    ur = get_record_state(user_id, asset_id, record_key, db)
    if not ur:
        # Create with default state
        default = {"status": "new", "ease_factor": 2.5, "interval_days": 1,
                   "times_reviewed": 0, "next_due": None, "last_reviewed": None}
        ur = get_or_create_record_state(user_id, asset_id, record_key, default, db)

    state = dict(ur.state or {})
    ease = float(state.get("ease_factor", 2.5))
    interval = int(state.get("interval_days", 1))

    if difficulty == "easy":
        interval = max(1, int(interval * 2.5))
        ease = min(2.5, ease + 0.1)
    elif difficulty == "medium":
        interval = max(1, int(interval * ease))
    elif difficulty == "hard":
        interval = 1
        ease = max(1.3, ease - 0.2)

    now = datetime.utcnow()
    next_due = (now + timedelta(days=interval)).strftime("%Y-%m-%d")

    state.update({
        "status": "active",
        "ease_factor": round(ease, 2),
        "interval_days": interval,
        "times_reviewed": state.get("times_reviewed", 0) + 1,
        "last_reviewed": now.strftime("%Y-%m-%d"),
        "next_due": next_due,
    })

    ur.state = state
    ur.updated_at = now

    # Update UserMeta (streak + total_solved)
    _update_user_meta(user_id, asset_id, db)

    db.commit()
    db.refresh(ur)
    return ur


def _update_user_meta(user_id: str, asset_id: str, db: Session) -> UserMeta:
    """Recalculate and save aggregate stats for a user+asset pair."""
    um = db.query(UserMeta).filter(
        UserMeta.user_id == user_id,
        UserMeta.asset_id == asset_id,
    ).first()

    if not um:
        from task_engine.models import _uuid
        um = UserMeta(id=_uuid(), user_id=user_id, asset_id=asset_id, meta={})
        db.add(um)

    all_records = db.query(UserRecord).filter(
        UserRecord.user_id == user_id,
        UserRecord.asset_id == asset_id,
    ).all()

    total_reviewed = sum(1 for r in all_records if r.state.get("times_reviewed", 0) > 0)
    today_str = date.today().isoformat()
    yesterday_str = (date.today() - timedelta(days=1)).isoformat()
    meta = dict(um.meta or {})
    last_activity = meta.get("last_activity", "")

    if last_activity == today_str:
        pass  # Already counted today
    elif last_activity == yesterday_str:
        meta["streak_days"] = meta.get("streak_days", 0) + 1
    else:
        meta["streak_days"] = 1

    meta["last_activity"] = today_str
    meta["total_solved"] = total_reviewed

    um.meta = meta
    um.updated_at = datetime.utcnow()
    db.commit()
    return um


# ── Stats + analytics ─────────────────────────────────────────────────────────

def get_user_stats(user_id: str, asset_id: str, db: Session) -> Dict[str, Any]:
    """Return aggregate progress stats for a user+asset."""
    all_asset_records = list_asset_records(asset_id, db)
    total = len(all_asset_records)

    user_records_map = {
        ur.record_key: ur for ur in db.query(UserRecord).filter(
            UserRecord.user_id == user_id,
            UserRecord.asset_id == asset_id,
        ).all()
    }

    new_count = 0
    active_count = 0
    mastered_count = 0
    total_reviewed = 0
    pattern_stats: Dict[str, Dict] = {}

    for rec in all_asset_records:
        ur = user_records_map.get(rec.record_key)
        state = ur.state if ur else {}
        status = state.get("status", "new")

        if status == "new":
            new_count += 1
        elif status == "active":
            active_count += 1
        elif status == "mastered":
            mastered_count += 1

        if state.get("times_reviewed", 0) > 0:
            total_reviewed += 1

        # Pattern-level analysis
        pattern = rec.data.get("pattern", "Unknown")
        if pattern not in pattern_stats:
            pattern_stats[pattern] = {"count": 0, "ease_sum": 0.0, "reviewed": 0}
        pattern_stats[pattern]["count"] += 1
        pattern_stats[pattern]["ease_sum"] += state.get("ease_factor", 2.5)
        if state.get("times_reviewed", 0) > 3 and state.get("ease_factor", 2.5) < 1.8:
            pattern_stats[pattern]["reviewed"] = pattern_stats[pattern].get("reviewed", 0) + 1

    # Weak patterns: avg ease < 1.8 and multiple reviews
    weak_patterns = [
        {"pattern": p, "avg_ease": round(v["ease_sum"] / v["count"], 2),
         "struggling_count": v["reviewed"]}
        for p, v in pattern_stats.items()
        if v["reviewed"] > 0 and v["ease_sum"] / v["count"] < 1.8
    ]
    weak_patterns.sort(key=lambda x: x["avg_ease"])

    um = db.query(UserMeta).filter(
        UserMeta.user_id == user_id,
        UserMeta.asset_id == asset_id,
    ).first()
    meta = um.meta if um else {}

    return {
        "user_id": user_id,
        "asset_id": asset_id,
        "total_records": total,
        "new_count": new_count,
        "active_count": active_count,
        "mastered_count": mastered_count,
        "total_reviewed": total_reviewed,
        "streak_days": meta.get("streak_days", 0),
        "total_solved": meta.get("total_solved", 0),
        "last_activity": meta.get("last_activity"),
        "weak_patterns": weak_patterns,
    }


# ── Interaction helpers ───────────────────────────────────────────────────────

def log_interaction(user_id: str, event_type: str, event_data: dict,
                    asset_id: Optional[str] = None, record_key: Optional[str] = None,
                    db: Session = None) -> Interaction:
    """Log any user event to the Interaction table."""
    from task_engine.models import _uuid
    interaction = Interaction(
        id=_uuid(),
        user_id=user_id,
        asset_id=asset_id,
        record_key=record_key,
        event_type=event_type,
        event_data=event_data,
    )
    db.add(interaction)
    db.commit()
    return interaction


# ── Executor context builder ──────────────────────────────────────────────────

def build_asset_context(db: Session) -> Dict[str, Any]:
    """
    Return a dict of DB-native functions to inject into the task executor context.
    Each function is partially applied with the db session so scripts call them without it.
    """
    return {
        # Users
        "get_user":             partial(get_user, db=db),
        "get_user_by_id":       partial(get_user_by_id, db=db),
        "get_or_create_user":   partial(get_or_create_user, db=db),

        # Assets
        "get_asset":            partial(get_asset, db=db),
        "list_asset_records":   partial(list_asset_records, db=db),

        # User Records
        "get_record_state":     partial(get_record_state, db=db),
        "get_next_record":      partial(get_next_record, db=db),
        "get_due_records":      partial(get_due_records, db=db),
        "apply_review":         partial(apply_review, db=db),

        # Stats
        "get_user_stats":       partial(get_user_stats, db=db),

        # Interactions
        "log_interaction":      partial(log_interaction, db=db),
    }
