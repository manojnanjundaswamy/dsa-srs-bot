import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from task_engine.database import get_db
from task_engine.executor import run_task
from task_engine.generator import generate_script
from task_engine.models import Task
from task_engine.schemas import (
    GenerateAndCreateRequest,
    GenerateRequest,
    GenerateResponse,
    TaskCreate,
    TaskResponse,
    TaskRunResponse,
    TaskUpdate,
)
from task_engine import scheduler as sched

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


def _get_task_or_404(task_id: str, db: Session) -> Task:
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task


@router.get("", response_model=List[TaskResponse])
def list_tasks(
    type: Optional[str] = None,
    enabled: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    q = db.query(Task)
    if type:
        q = q.filter(Task.type == type)
    if enabled is not None:
        q = q.filter(Task.enabled == enabled)
    return q.order_by(Task.created_at).all()


@router.post("", response_model=TaskResponse, status_code=201)
def create_task(body: TaskCreate, db: Session = Depends(get_db)):
    task = Task(
        id=str(uuid.uuid4()),
        name=body.name,
        description=body.description,
        type=body.type,
        trigger_config=body.trigger_config,
        script=body.script,
        script_args=body.script_args,
        prompt=body.prompt,
        enabled=body.enabled,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    if task.enabled and task.type in ("cron", "interval"):
        sched.add_job(task)

    return task


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: str, db: Session = Depends(get_db)):
    return _get_task_or_404(task_id, db)


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(task_id: str, body: TaskUpdate, db: Session = Depends(get_db)):
    task = _get_task_or_404(task_id, db)

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)

    # Re-register in scheduler (handles enable/disable changes too)
    sched.remove_job(task.id)
    if task.enabled and task.type in ("cron", "interval"):
        sched.add_job(task)

    return task


@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: str, db: Session = Depends(get_db)):
    task = _get_task_or_404(task_id, db)
    sched.remove_job(task.id)
    db.delete(task)
    db.commit()


@router.post("/{task_id}/run", response_model=TaskRunResponse)
def manual_run(task_id: str, db: Session = Depends(get_db)):
    """Trigger a task immediately regardless of its schedule."""
    task = _get_task_or_404(task_id, db)
    run = run_task(task, db, triggered_by="manual")
    return run


@router.post("/{task_id}/duplicate", response_model=TaskResponse, status_code=201)
def duplicate_task(task_id: str, db: Session = Depends(get_db)):
    """Copy a task. The copy is disabled by default to avoid accidental double-runs."""
    original = _get_task_or_404(task_id, db)
    copy = Task(
        id=str(uuid.uuid4()),
        name=f"Copy of {original.name}"[:255],
        description=original.description,
        type=original.type,
        trigger_config=original.trigger_config,
        script=original.script,
        script_args=original.script_args,
        prompt=original.prompt,
        enabled=False,  # disabled by default — user enables explicitly
        parent_task_id=original.id,
    )
    db.add(copy)
    db.commit()
    db.refresh(copy)
    return copy


@router.post("/{task_id}/enable", response_model=TaskResponse)
def enable_task(task_id: str, db: Session = Depends(get_db)):
    task = _get_task_or_404(task_id, db)
    task.enabled = True
    db.commit()
    db.refresh(task)
    if task.type in ("cron", "interval"):
        sched.add_job(task)
    return task


@router.post("/{task_id}/disable", response_model=TaskResponse)
def disable_task(task_id: str, db: Session = Depends(get_db)):
    task = _get_task_or_404(task_id, db)
    task.enabled = False
    db.commit()
    db.refresh(task)
    sched.remove_job(task.id)
    return task


# ── Script generation endpoints ───────────────────────────────────────────────

@router.post("/generate", response_model=GenerateResponse)
def generate(body: GenerateRequest):
    """Use Claude to generate a Python script from a natural language prompt."""
    result = generate_script(body.prompt, body.context_hint)
    return GenerateResponse(
        script=result["script"],
        suggested_name=result["suggested_name"],
        suggested_type=result["suggested_type"],
        suggested_trigger=result["suggested_trigger"],
    )


@router.post("/generate-and-create", response_model=TaskResponse, status_code=201)
def generate_and_create(body: GenerateAndCreateRequest, db: Session = Depends(get_db)):
    """Generate a script from a prompt and immediately save it as a new Task."""
    result = generate_script(body.prompt)

    task = Task(
        id=str(uuid.uuid4()),
        name=result["suggested_name"],
        description=body.prompt,
        type=body.type,
        trigger_config=body.trigger_config or result["suggested_trigger"],
        script=result["script"],
        script_args=body.script_args,
        prompt=body.prompt,
        enabled=body.enabled,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    if task.enabled and task.type in ("cron", "interval"):
        sched.add_job(task)

    return task
