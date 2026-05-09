"""
APScheduler wrapper.

Manages cron and interval jobs whose definitions live in the Task table.
Event and manual tasks are not registered here — they fire via the API.
"""

import logging
from datetime import datetime
from typing import List, Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session

from task_engine.models import Task

logger = logging.getLogger(__name__)

# Module-level scheduler instance shared across the application
_scheduler: Optional[BackgroundScheduler] = None


def get_scheduler() -> BackgroundScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler(timezone="UTC")
    return _scheduler


def _make_job_id(task_id: str) -> str:
    return f"task_{task_id}"


def _job_func(task_id: str) -> None:
    """Executed by APScheduler for each scheduled job."""
    from task_engine.database import SessionLocal
    from task_engine.executor import run_task

    db: Session = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id, Task.enabled == True).first()  # noqa: E712
        if task:
            run = run_task(task, db, triggered_by="scheduler")
            status = run.status
            logger.info(f"Scheduled run completed: task={task.name} status={status}")
        else:
            logger.warning(f"Scheduled job fired but task {task_id} not found or disabled")
    except Exception as e:
        logger.error(f"Error in scheduled job for task {task_id}: {e}")
        # Best-effort: record a failed TaskRun so the failure is visible in the UI
        try:
            from task_engine.models import TaskRun
            failed_run = TaskRun(
                task_id=task_id,
                triggered_by="scheduler",
                status="failed",
                error=str(e),
                completed_at=datetime.utcnow(),
            )
            db.add(failed_run)
            # Also update last_run_status on the task
            task_row = db.query(Task).filter(Task.id == task_id).first()
            if task_row:
                task_row.last_run_at = datetime.utcnow()
                task_row.last_run_status = "failed"
            db.commit()
        except Exception as inner_e:
            logger.error(f"Could not record failed run for task {task_id}: {inner_e}")
    finally:
        db.close()


def add_job(task: Task) -> None:
    """Register a task with the scheduler. Replaces any existing job for this task."""
    scheduler = get_scheduler()
    job_id = _make_job_id(task.id)

    # Remove existing job if present
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)

    if not task.enabled:
        return

    cfg = task.trigger_config or {}

    if task.type == "cron":
        cron_expr = cfg.get("cron", "0 0 * * *")
        timezone = cfg.get("timezone", "Asia/Kolkata")
        parts = cron_expr.split()
        if len(parts) == 5:
            minute, hour, day, month, day_of_week = parts
        else:
            # Fallback: treat as daily at midnight
            minute, hour, day, month, day_of_week = "0", "0", "*", "*", "*"

        trigger = CronTrigger(
            minute=minute, hour=hour, day=day,
            month=month, day_of_week=day_of_week,
            timezone=timezone,
        )
        scheduler.add_job(_job_func, trigger, id=job_id, args=[task.id],
                          name=task.name, replace_existing=True)
        logger.info(f"Cron job registered: {task.name} [{cron_expr} {timezone}]")

    elif task.type == "interval":
        seconds = int(cfg.get("interval_seconds", 60))
        trigger = IntervalTrigger(seconds=seconds)
        scheduler.add_job(_job_func, trigger, id=job_id, args=[task.id],
                          name=task.name, replace_existing=True)
        logger.info(f"Interval job registered: {task.name} [every {seconds}s]")

    # event and manual types are not registered with APScheduler


def remove_job(task_id: str) -> None:
    """Unregister a task from the scheduler."""
    scheduler = get_scheduler()
    job_id = _make_job_id(task_id)
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        logger.info(f"Job removed from scheduler: task_id={task_id}")


def load_all_jobs(db: Session) -> int:
    """Load all enabled schedulable tasks from the DB into APScheduler."""
    tasks: List[Task] = db.query(Task).filter(
        Task.enabled == True,  # noqa: E712
        Task.type.in_(["cron", "interval"]),
    ).all()

    for task in tasks:
        add_job(task)

    return len(tasks)


def reload_jobs(db: Session) -> int:
    """Clear all existing jobs and reload from DB."""
    scheduler = get_scheduler()
    scheduler.remove_all_jobs()
    return load_all_jobs(db)


def start() -> None:
    scheduler = get_scheduler()
    if not scheduler.running:
        scheduler.start()
        logger.info("APScheduler started")


def stop() -> None:
    scheduler = get_scheduler()
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler stopped")


def get_status(db: Session) -> dict:
    """
    Return scheduler status including per-job last_run_at and next_run_time.
    last_run_at comes from Task.last_run_at (updated by executor).
    next_run_time comes from APScheduler's live job object.
    """
    scheduler = get_scheduler()
    jobs_info = []

    tasks: List[Task] = db.query(Task).filter(Task.enabled == True).all()  # noqa: E712

    for task in tasks:
        job = scheduler.get_job(_make_job_id(task.id))
        next_run: Optional[datetime] = job.next_run_time if job else None

        # Build a human-readable trigger description
        cfg = task.trigger_config or {}
        if task.type == "cron":
            tz = cfg.get("timezone", "Asia/Kolkata")
            trigger_desc = f"{cfg.get('cron', '?')} ({tz})"
        elif task.type == "interval":
            trigger_desc = f"every {cfg.get('interval_seconds', '?')}s"
        elif task.type == "event":
            trigger_desc = f"event:{cfg.get('event_key', '?')}"
        else:
            trigger_desc = "manual"

        jobs_info.append({
            "task_id": task.id,
            "task_name": task.name,
            "type": task.type,
            "trigger_description": trigger_desc,
            "enabled": task.enabled,
            "last_run_at": task.last_run_at,
            "next_run_time": next_run,
        })

    return {
        "running": scheduler.running,
        "job_count": len(scheduler.get_jobs()),
        "jobs": jobs_info,
    }
