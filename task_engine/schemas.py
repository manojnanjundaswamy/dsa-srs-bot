from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

CFG = {"from_attributes": True}

# ── Task schemas ──────────────────────────────────────────────────────────────

class TaskCreate(BaseModel):
    name: str
    description: str = ""
    type: str
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
    model_config = CFG


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
    events: List[Dict[str, Any]] = []
    model_config = CFG


# ── Script generation schemas ─────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    prompt: str
    context_hint: str = ""


class GenerateResponse(BaseModel):
    script: str
    suggested_name: str
    suggested_type: str
    suggested_trigger: Dict[str, Any]


class GenerateAndCreateRequest(BaseModel):
    prompt: str
    type: str
    trigger_config: Dict[str, Any] = Field(default_factory=dict)
    script_args: Dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True


# ── Scheduler schemas ─────────────────────────────────────────────────────────

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


# ── Event webhook schema ──────────────────────────────────────────────────────

class EventPayload(BaseModel):
    data: Dict[str, Any] = Field(default_factory=dict)


# ── Asset schemas ─────────────────────────────────────────────────────────────

class AssetCreate(BaseModel):
    name: str
    type: str = "generic"
    description: str = ""
    record_schema: Dict[str, Any] = Field(default_factory=dict)


class AssetUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = None
    record_schema: Optional[Dict[str, Any]] = None


class AssetResponse(BaseModel):
    id: str
    name: str
    type: str
    description: str
    record_schema: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    model_config = CFG


# ── AssetRecord schemas ───────────────────────────────────────────────────────

class AssetRecordCreate(BaseModel):
    record_key: str
    data: Dict[str, Any] = Field(default_factory=dict)
    order: int = 0


class AssetRecordUpdate(BaseModel):
    data: Optional[Dict[str, Any]] = None
    order: Optional[int] = None


class AssetRecordResponse(BaseModel):
    id: str
    asset_id: str
    record_key: str
    data: Dict[str, Any]
    order: int
    created_at: datetime
    updated_at: datetime
    model_config = CFG


# ── User schemas ──────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    name: str
    telegram_chat_id: Optional[str] = None
    metadata_: Dict[str, Any] = Field(default_factory=dict, alias="metadata")
    enabled: bool = True
    model_config = {"populate_by_name": True}


class UserUpdate(BaseModel):
    name: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    metadata_: Optional[Dict[str, Any]] = Field(default=None, alias="metadata")
    enabled: Optional[bool] = None
    model_config = {"populate_by_name": True}


class UserResponse(BaseModel):
    id: str
    name: str
    telegram_chat_id: Optional[str]
    metadata: Optional[Dict[str, Any]] = Field(default=None, alias="metadata_")
    enabled: bool
    created_at: datetime
    model_config = {"from_attributes": True, "populate_by_name": True}


# ── UserRecord schemas ────────────────────────────────────────────────────────

class UserRecordStateUpdate(BaseModel):
    state: Dict[str, Any]  # partial merge applied on the server


class UserRecordResponse(BaseModel):
    id: str
    user_id: str
    asset_id: str
    record_key: str
    state: Dict[str, Any]
    updated_at: datetime
    created_at: datetime
    model_config = CFG


class RecordWithState(BaseModel):
    """AssetRecord merged with the user's UserRecord state."""
    record_key: str
    data: Dict[str, Any]
    order: int
    state: Optional[Dict[str, Any]] = None   # None if user has no state yet
    model_config = CFG


# ── UserMeta schemas ──────────────────────────────────────────────────────────

class UserMetaResponse(BaseModel):
    user_id: str
    asset_id: str
    meta: Dict[str, Any]
    updated_at: datetime
    model_config = CFG


# ── TaskAsset schemas ─────────────────────────────────────────────────────────

class TaskAssetLink(BaseModel):
    asset_id: str
    role: str = "read"  # read | write | context


class TaskAssetResponse(BaseModel):
    task_id: str
    asset_id: str
    role: str
    asset_name: Optional[str] = None
    model_config = CFG


# ── SM-2 review schemas ───────────────────────────────────────────────────────

class ReviewRequest(BaseModel):
    difficulty: str  # "easy" | "medium" | "hard"


class ReviewResponse(BaseModel):
    record_key: str
    new_state: Dict[str, Any]
    next_due: Optional[str]


# ── UserStats schemas ─────────────────────────────────────────────────────────

class UserStatsResponse(BaseModel):
    user_id: str
    asset_id: str
    total_records: int
    new_count: int
    active_count: int
    mastered_count: int
    total_reviewed: int
    streak_days: int
    total_solved: int
    last_activity: Optional[str]
    weak_patterns: List[Dict[str, Any]]  # [{pattern, count}]


# ── Interaction schemas ───────────────────────────────────────────────────────

class InteractionCreate(BaseModel):
    user_id: str
    asset_id: Optional[str] = None
    record_key: Optional[str] = None
    event_type: str  # "review" | "question" | "button_tap" | "feedback" | "hint"
    event_data: Dict[str, Any] = Field(default_factory=dict)


class InteractionResponse(BaseModel):
    id: str
    user_id: str
    asset_id: Optional[str]
    record_key: Optional[str]
    event_type: str
    event_data: Dict[str, Any]
    created_at: datetime
    model_config = CFG
