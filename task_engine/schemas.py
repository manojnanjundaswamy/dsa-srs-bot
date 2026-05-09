from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ── Task schemas ─────────────────────────────────────────────────────────────

class TaskCreate(BaseModel):
    name: str
    description: str = ""
    type: str  # cron | interval | event | manual
    trigger_config: Dict[str, Any] = Field(default_factory=dict)
    script: str
    script_args: Dict[str, Any] = Field(default_factory=dict)
    prompt: str = ""
    enabled: bool = True


class TaskUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    trigger_config: Optional[Dict[str, Any]] = None
    script: Optional[str] = None
    script_args: Optional[Dict[str, Any]] = None
    prompt: Optional[str] = None
    enabled: Optional[bool] = None


class TaskResponse(BaseModel):
    id: str
    name: str
    description: str
    type: str
    trigger_config: Dict[str, Any]
    script: str
    script_args: Dict[str, Any]
    prompt: str
    enabled: bool
    parent_task_id: Optional[str]
    last_run_at: Optional[datetime]
    last_run_status: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── TaskRun schemas ───────────────────────────────────────────────────────────

class TaskRunResponse(BaseModel):
    id: str
    task_id: str
    triggered_by: str
    started_at: datetime
    completed_at: Optional[datetime]
    status: str
    output: str
    error: Optional[str]

    model_config = {"from_attributes": True}


# ── Script generation schemas ─────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    prompt: str
    context_hint: str = ""  # optional extra context (e.g., "telegram bot, DSA problems")


class GenerateResponse(BaseModel):
    script: str
    suggested_name: str
    suggested_type: str       # cron | interval | event | manual
    suggested_trigger: Dict[str, Any]


class GenerateAndCreateRequest(BaseModel):
    prompt: str
    type: str
    trigger_config: Dict[str, Any] = Field(default_factory=dict)
    script_args: Dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True


# ── Scheduler status schemas ──────────────────────────────────────────────────

class SchedulerJobStatus(BaseModel):
    task_id: str
    task_name: str
    type: str
    trigger_description: str
    enabled: bool
    last_run_at: Optional[datetime]
    next_run_time: Optional[datetime]


class SchedulerStatusResponse(BaseModel):
    running: bool
    job_count: int
    jobs: List[SchedulerJobStatus]


# ── Asset schemas ─────────────────────────────────────────────────────────────

class AssetCreate(BaseModel):
    name: str
    type: str
    data: Dict[str, Any] = Field(default_factory=dict)


class AssetResponse(BaseModel):
    id: str
    name: str
    type: str
    data: Dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Event webhook schema ──────────────────────────────────────────────────────

class EventPayload(BaseModel):
    data: Dict[str, Any] = Field(default_factory=dict)
