"""
Task Engine — FastAPI entry point.

Start with:
    uvicorn task_engine.api:app --host 127.0.0.1 --port 8080

API docs available at: http://127.0.0.1:8080/docs
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from task_engine import scheduler as sched
from task_engine.database import SessionLocal, get_db, init_db
from task_engine.models import Asset, AssetRecord, Task, User, UserRecord, UserMeta
from task_engine.routers import assets as assets_router
from task_engine.routers import events, interactions, runs, tasks
from task_engine.routers import users as users_router
from task_engine.schemas import SchedulerStatusResponse

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)

# ── Seed tasks (migrated from reminder_bot.py modes) ─────────────────────────

SEED_TASKS = [
    {
        "id": "dsa-morning",
        "name": "DSA Morning Session",
        "description": "Sends morning pattern + problem message to Telegram at 7 AM",
        "type": "cron",
        "trigger_config": {"cron": "0 7 * * *", "timezone": "Asia/Kolkata"},
        "script": "morning_mode()",
        "script_args": {},
        "prompt": "Send DSA morning prep message to Telegram at 7 AM daily",
        "enabled": True,
    },
    {
        "id": "dsa-afternoon",
        "name": "DSA Afternoon Session",
        "description": "Sends afternoon problem + adaptive buttons to Telegram at 3 PM",
        "type": "cron",
        "trigger_config": {"cron": "0 15 * * *", "timezone": "Asia/Kolkata"},
        "script": "afternoon_mode()",
        "script_args": {},
        "prompt": "Send DSA afternoon problem-solving session message to Telegram at 3 PM",
        "enabled": True,
    },
    {
        "id": "dsa-evening",
        "name": "DSA Evening Review",
        "description": "Sends evening SRS review reminder to Telegram at 7 PM",
        "type": "cron",
        "trigger_config": {"cron": "0 19 * * *", "timezone": "Asia/Kolkata"},
        "script": "evening_mode()",
        "script_args": {},
        "prompt": "Send DSA evening review reminder to Telegram at 7 PM",
        "enabled": True,
    },
    {
        "id": "dsa-night",
        "name": "DSA Night Summary",
        "description": "Sends night summary with tomorrow's preview at 10 PM",
        "type": "cron",
        "trigger_config": {"cron": "0 22 * * *", "timezone": "Asia/Kolkata"},
        "script": "night_mode()",
        "script_args": {},
        "prompt": "Send DSA night summary with tomorrow's problem preview at 10 PM",
        "enabled": True,
    },
    {
        "id": "telegram-listener",
        "name": "Telegram Message Listener",
        "description": "Polls Telegram every 10 seconds for button taps and text messages",
        "type": "interval",
        "trigger_config": {"interval_seconds": 10},
        "script": "poll_mode()",
        "script_args": {},
        "prompt": "Poll Telegram every 10 seconds for messages and button taps",
        "enabled": True,
    },
]


def _seed_tasks(db: Session) -> None:
    """Insert any missing seed tasks (checks by ID, not count)."""
    seed_ids = [t["id"] for t in SEED_TASKS]
    existing_ids = {row[0] for row in db.query(Task.id).filter(Task.id.in_(seed_ids)).all()}
    to_insert = [t for t in SEED_TASKS if t["id"] not in existing_ids]

    if not to_insert:
        logger.info("All seed tasks already present — skipping seed")
        return

    for t in to_insert:
        task = Task(
            id=t["id"],
            name=t["name"],
            description=t.get("description", ""),
            type=t["type"],
            trigger_config=t.get("trigger_config", {}),
            script=t["script"],
            script_args=t.get("script_args", {}),
            prompt=t.get("prompt", ""),
            enabled=t.get("enabled", True),
        )
        db.add(task)

    db.commit()
    logger.info(f"{len(to_insert)} seed task(s) inserted")


# ── Asset + User seeding ──────────────────────────────────────────────────────

def _seed_assets(db: Session) -> None:
    """
    Seed the default user and DSA Problem Set asset from dsa_tracker.json.
    Idempotent — safe to call on every startup.
    """
    import json
    import os
    from pathlib import Path

    tracker_path = Path(__file__).parent.parent / "dsa_tracker.json"
    if not tracker_path.exists():
        logger.warning("dsa_tracker.json not found — skipping asset seed")
        return

    with open(tracker_path, encoding="utf-8") as f:
        tracker = json.load(f)

    # 1. Default user — from env or fallback
    chat_id = os.getenv("TELEGRAM_CHAT_ID") or os.getenv("CHAT_ID", "5466701469")
    user = db.query(User).filter(User.telegram_chat_id == chat_id).first()
    if not user:
        import uuid as _uuid
        user = User(
            id=str(_uuid.uuid4()),
            name="Manoj",
            telegram_chat_id=chat_id,
            metadata_={},
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"Default user seeded: {user.name} (chat_id={chat_id})")
    else:
        logger.info(f"Default user already exists: {user.name}")

    # 2. DSA Problem Set asset
    DSA_ASSET_NAME = "DSA Problem Set"
    asset = db.query(Asset).filter(Asset.name == DSA_ASSET_NAME).first()
    if not asset:
        import uuid as _uuid
        asset = Asset(
            id=str(_uuid.uuid4()),
            name=DSA_ASSET_NAME,
            type="problem_set",
            description="NeetCode 175 — curated DSA problem roadmap with SM-2 spaced repetition",
            record_schema={
                "fields": ["id", "title", "leetcode_url", "leetcode_number",
                           "pattern", "difficulty"]
            },
        )
        db.add(asset)
        db.commit()
        db.refresh(asset)
        logger.info(f"Asset created: '{DSA_ASSET_NAME}' (id={asset.id})")
    else:
        logger.info(f"Asset already exists: '{DSA_ASSET_NAME}'")

    # 3. AssetRecords — one per problem
    problems = tracker.get("problems", [])
    existing_keys = {
        r.record_key
        for r in db.query(AssetRecord.record_key).filter(AssetRecord.asset_id == asset.id).all()
    }
    new_records = 0
    for idx, p in enumerate(problems):
        key = p.get("id") or p["title"].lower().replace(" ", "-")
        if key in existing_keys:
            continue
        rec = AssetRecord(
            id=str(__import__("uuid").uuid4()),
            asset_id=asset.id,
            record_key=key,
            order=idx,
            data={
                "title":            p.get("title"),
                "leetcode_url":     p.get("leetcode_url"),
                "leetcode_number":  p.get("leetcode_number"),
                "pattern":          p.get("pattern"),
                "difficulty":       p.get("difficulty"),
            },
        )
        db.add(rec)
        new_records += 1

    if new_records:
        db.commit()
        logger.info(f"Seeded {new_records} AssetRecord(s) into '{DSA_ASSET_NAME}'")

    # 4. UserRecord — one per problem, seeded from current JSON SM-2 state
    existing_ur_keys = {
        ur.record_key
        for ur in db.query(UserRecord.record_key).filter(
            UserRecord.user_id == user.id,
            UserRecord.asset_id == asset.id,
        ).all()
    }
    new_urs = 0
    for p in problems:
        key = p.get("id") or p["title"].lower().replace(" ", "-")
        if key in existing_ur_keys:
            continue
        ur = UserRecord(
            id=str(__import__("uuid").uuid4()),
            user_id=user.id,
            asset_id=asset.id,
            record_key=key,
            state={
                "status":          p.get("status", "new"),
                "ease_factor":     p.get("ease_factor", 2.5),
                "interval_days":   p.get("interval_days", 1),
                "times_reviewed":  p.get("times_reviewed", 0),
                "last_reviewed":   p.get("last_reviewed"),
                "next_due":        p.get("next_due"),
            },
        )
        db.add(ur)
        new_urs += 1

    if new_urs:
        db.commit()
        logger.info(f"Seeded {new_urs} UserRecord(s) for user '{user.name}'")

    # 5. UserMeta — overall stats
    meta = tracker.get("metadata", {})
    um = db.query(UserMeta).filter(
        UserMeta.user_id == user.id,
        UserMeta.asset_id == asset.id,
    ).first()
    if not um:
        um = UserMeta(
            id=str(__import__("uuid").uuid4()),
            user_id=user.id,
            asset_id=asset.id,
            meta={
                "streak_days":   meta.get("streak_days", 0),
                "total_solved":  meta.get("total_problems_solved", 0),
                "last_activity": meta.get("last_updated"),
                "current_week":  meta.get("current_week", 1),
                "current_pattern": meta.get("current_pattern", ""),
            },
        )
        db.add(um)
        db.commit()
        logger.info(f"UserMeta seeded for '{user.name}'")


# ── App lifespan ──────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Task Engine starting up")
    init_db()

    db = SessionLocal()
    try:
        _seed_tasks(db)
        _seed_assets(db)
        job_count = sched.load_all_jobs(db)
        logger.info(f"Loaded {job_count} schedulable job(s) from DB")
    finally:
        db.close()

    sched.start()
    logger.info("Scheduler started — task engine is live")

    yield  # app runs here

    # Shutdown
    sched.stop()
    logger.info("Task Engine shut down cleanly")


# ── FastAPI app ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="Task Engine",
    description="Configurable workflow automation for the DSA bot. "
                "Tasks stored in SQLite (PostgreSQL-migratable), "
                "scheduled via APScheduler, scripts generated by Claude.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten for production
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(tasks.router)
app.include_router(runs.router)
app.include_router(events.router)
app.include_router(assets_router.router)
app.include_router(users_router.router)
app.include_router(interactions.router)


# ── Scheduler endpoints ───────────────────────────────────────────────────────

@app.get("/api/scheduler/status", response_model=SchedulerStatusResponse, tags=["scheduler"])
def scheduler_status(db: Session = Depends(get_db)):
    """
    Return current scheduler state with per-job last_run_at and next_run_time.
    """
    status = sched.get_status(db)
    return SchedulerStatusResponse(**status)


@app.post("/api/scheduler/reload", tags=["scheduler"])
def scheduler_reload(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Re-sync all scheduler jobs from the database (use after manual DB edits)."""
    count = sched.reload_jobs(db)
    return {"reloaded_jobs": count}


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/health", tags=["meta"])
def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "scheduler_running": sched.get_scheduler().running,
    }
