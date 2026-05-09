from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from task_engine.database import get_db
from task_engine.executor import run_task
from task_engine.models import Task
from task_engine.schemas import EventPayload, TaskRunResponse

router = APIRouter(prefix="/api/events", tags=["events"])


@router.post("/{task_id}", response_model=TaskRunResponse)
def trigger_event(
    task_id: str,
    payload: EventPayload,
    db: Session = Depends(get_db),
):
    """
    Webhook endpoint for event-type tasks.

    POST /api/events/{task_id}
    Body: {"data": {"key": "value"}}

    The payload.data dict is available as `event` inside the task script.
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    if not task.enabled:
        raise HTTPException(status_code=409, detail=f"Task {task_id} is disabled")
    if task.type != "event":
        raise HTTPException(
            status_code=400,
            detail=f"Task {task_id} has type '{task.type}', not 'event'"
        )

    run = run_task(task, db, triggered_by="event", event_data=payload.data)
    return run
