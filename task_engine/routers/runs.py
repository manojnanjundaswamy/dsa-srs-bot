from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from task_engine.database import get_db
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
