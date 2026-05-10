import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from task_engine.database import SessionLocal, get_db
from task_engine.models import Task, TaskRun
from task_engine.schemas import TaskRunResponse

router = APIRouter(prefix="/api", tags=["runs"])


@router.get("/runs", response_model=List[TaskRunResponse])
def list_all_runs(
    limit: int = Query(default=30, le=200),
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Return recent execution history across ALL tasks, latest first."""
    q = db.query(TaskRun)
    if status:
        q = q.filter(TaskRun.status == status)
    return q.order_by(TaskRun.started_at.desc()).limit(limit).all()


@router.get("/tasks/{task_id}/runs", response_model=List[TaskRunResponse])
def list_task_runs(
    task_id: str,
    limit: int = Query(default=20, le=100),
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Return execution history for a specific task, latest first."""
    q = db.query(TaskRun).filter(TaskRun.task_id == task_id)
    if status:
        q = q.filter(TaskRun.status == status)
    return q.order_by(TaskRun.started_at.desc()).limit(limit).all()


@router.get("/runs/{run_id}", response_model=TaskRunResponse)
def get_run(run_id: str, db: Session = Depends(get_db)):
    run = db.query(TaskRun).filter(TaskRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return run


@router.get("/runs/{run_id}/stream")
def stream_run_events(run_id: str):
    """
    Server-Sent Events stream for a running task.
    Polls TaskRun.events every 500ms and pushes new events to the client.
    Closes automatically when the run reaches success or failed status.
    """

    def event_generator():
        last_count = 0
        max_polls = 120  # 60 seconds max

        for _ in range(max_polls):
            db = SessionLocal()
            try:
                run = db.query(TaskRun).filter(TaskRun.id == run_id).first()
                if not run:
                    yield f"event: error\ndata: {json.dumps({'msg': 'Run not found'})}\n\n"
                    return

                events = run.events or []
                # Push any new events since last poll
                new_events = events[last_count:]
                for ev in new_events:
                    yield f"event: log\ndata: {json.dumps(ev)}\n\n"
                last_count = len(events)

                # Send status ping
                yield f"event: status\ndata: {json.dumps({'status': run.status, 'count': last_count})}\n\n"

                if run.status in ("success", "failed"):
                    yield f"event: done\ndata: {json.dumps({'status': run.status})}\n\n"
                    return
            finally:
                db.close()

            time.sleep(0.5)

        yield f"event: done\ndata: {json.dumps({'status': 'timeout'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/analytics/runs-summary")
def runs_summary(
    days: int = Query(default=7, ge=1, le=90),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Returns daily run counts by status for the last N days.
    Response shape:
    {
      "days": [...date strings],
      "success": [...counts],
      "failed": [...counts],
      "total": [...counts]
    }
    Also returns per-task average duration for the last 10 runs.
    """
    since = datetime.utcnow() - timedelta(days=days)
    runs = (
        db.query(TaskRun)
        .filter(TaskRun.started_at >= since)
        .order_by(TaskRun.started_at.asc())
        .all()
    )

    # Build daily buckets
    day_buckets: Dict[str, Dict[str, int]] = {}
    for i in range(days):
        d = (datetime.utcnow() - timedelta(days=days - 1 - i)).strftime("%Y-%m-%d")
        day_buckets[d] = {"success": 0, "failed": 0, "running": 0}

    for run in runs:
        d = run.started_at.strftime("%Y-%m-%d")
        if d in day_buckets:
            day_buckets[d][run.status] = day_buckets[d].get(run.status, 0) + 1

    sorted_days = sorted(day_buckets.keys())

    # Per-task duration stats (last 10 completed runs per task)
    tasks = db.query(Task).filter(Task.enabled == True).all()  # noqa
    task_durations = []
    for task in tasks:
        recent = (
            db.query(TaskRun)
            .filter(
                TaskRun.task_id == task.id,
                TaskRun.status == "success",
                TaskRun.completed_at.isnot(None),
            )
            .order_by(TaskRun.started_at.desc())
            .limit(10)
            .all()
        )
        if not recent:
            continue
        durations = [
            int((r.completed_at - r.started_at).total_seconds() * 1000)
            for r in recent
            if r.completed_at
        ]
        if durations:
            task_durations.append({
                "task_id": task.id,
                "task_name": task.name,
                "avg_ms": round(sum(durations) / len(durations)),
                "min_ms": min(durations),
                "max_ms": max(durations),
                "samples": len(durations),
            })

    return {
        "days": sorted_days,
        "success": [day_buckets[d]["success"] for d in sorted_days],
        "failed":  [day_buckets[d].get("failed", 0) for d in sorted_days],
        "total":   [sum(day_buckets[d].values()) for d in sorted_days],
        "task_durations": task_durations,
    }
