import uuid
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.types import JSON
from sqlalchemy.orm import relationship
from task_engine.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


# ── Task + TaskRun (unchanged) ────────────────────────────────────────────────

class Task(Base):
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True, default=_uuid)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")

    # "cron" | "interval" | "event" | "manual"
    type = Column(String(32), nullable=False)

    # {"cron": "0 7 * * *", "timezone": "Asia/Kolkata"} | {"interval_seconds": 10} | {}
    trigger_config = Column(JSON, default=dict)

    # Python code stored as text; executed via exec() at runtime
    script = Column(Text, nullable=False)

    # JSON dict injected as `args` variable inside exec context
    script_args = Column(JSON, default=dict)

    # Natural language prompt that generated the script
    prompt = Column(Text, default="")

    enabled = Column(Boolean, default=True, index=True)

    parent_task_id = Column(String(36), ForeignKey("tasks.id"), nullable=True)

    # Denormalized from the last TaskRun
    last_run_at = Column(DateTime, nullable=True)
    last_run_status = Column(String(16), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    runs = relationship("TaskRun", back_populates="task", cascade="all, delete-orphan")
    asset_links = relationship("TaskAsset", back_populates="task", cascade="all, delete-orphan")


class TaskRun(Base):
    __tablename__ = "task_runs"

    id = Column(String(36), primary_key=True, default=_uuid)
    task_id = Column(String(36), ForeignKey("tasks.id"), nullable=False, index=True)

    triggered_by = Column(String(32), nullable=False)

    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    status = Column(String(16), default="running")

    output = Column(Text, default="")
    error = Column(Text, nullable=True)

    # Structured execution trace: [{t, type, msg, level, ms?}]
    # t = milliseconds since task started; ms = duration for api_call events
    events = Column(JSON, default=list)

    task = relationship("Task", back_populates="runs")


# ── Asset layer ───────────────────────────────────────────────────────────────

class Asset(Base):
    """
    A named dataset (e.g. 'DSA Problem Set', 'Weekly Goals').
    Individual items live in AssetRecord.
    """
    __tablename__ = "assets"

    id = Column(String(36), primary_key=True, default=_uuid)
    name = Column(String(255), nullable=False)
    type = Column(String(64))          # "problem_set" | "config" | "schedule" | custom
    description = Column(Text, default="")
    record_schema = Column(JSON, default=dict)  # optional JSON Schema for validation
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    records = relationship("AssetRecord", back_populates="asset", cascade="all, delete-orphan")
    task_links = relationship("TaskAsset", back_populates="asset", cascade="all, delete-orphan")
    user_records = relationship("UserRecord", back_populates="asset", cascade="all, delete-orphan")
    user_metas = relationship("UserMeta", back_populates="asset", cascade="all, delete-orphan")
    interactions = relationship("Interaction", back_populates="asset")


class AssetRecord(Base):
    """
    One item within an Asset (one DSA problem, one config key, etc.).
    record_key is a stable slug/ID that UserRecord references.
    """
    __tablename__ = "asset_records"

    id = Column(String(36), primary_key=True, default=_uuid)
    asset_id = Column(String(36), ForeignKey("assets.id"), nullable=False, index=True)
    record_key = Column(String(255), nullable=False)  # stable slug, e.g. "contains-duplicate"
    data = Column(JSON, default=dict)                 # static item data (title, url, pattern…)
    order = Column(Integer, default=0)                # ordering within the asset
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    asset = relationship("Asset", back_populates="records")

    __table_args__ = (
        UniqueConstraint("asset_id", "record_key", name="uq_asset_record"),
    )


# ── User layer ────────────────────────────────────────────────────────────────

class User(Base):
    """A person who interacts with the system (via Telegram or API)."""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=_uuid)
    name = Column(String(255), nullable=False)
    telegram_chat_id = Column(String(64), unique=True, index=True)
    metadata_ = Column("metadata", JSON, default=dict)  # extra settings, timezone, etc.
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user_records = relationship("UserRecord", back_populates="user", cascade="all, delete-orphan")
    user_metas = relationship("UserMeta", back_populates="user", cascade="all, delete-orphan")
    interactions = relationship("Interaction", back_populates="user")


class UserRecord(Base):
    """
    A user's state/progress for one AssetRecord.
    For DSA: stores SM-2 fields (status, ease_factor, interval_days, next_due…).
    For any other asset: stores whatever state dict makes sense.
    """
    __tablename__ = "user_records"

    id = Column(String(36), primary_key=True, default=_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    asset_id = Column(String(36), ForeignKey("assets.id"), nullable=False, index=True)
    record_key = Column(String(255), nullable=False)  # references AssetRecord.record_key
    state = Column(JSON, default=dict)                # arbitrary state per record
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="user_records")
    asset = relationship("Asset", back_populates="user_records")

    __table_args__ = (
        UniqueConstraint("user_id", "asset_id", "record_key", name="uq_user_record"),
    )


class UserMeta(Base):
    """Aggregate stats for a user within a specific asset (streak, total_solved, etc.)."""
    __tablename__ = "user_meta"

    id = Column(String(36), primary_key=True, default=_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    asset_id = Column(String(36), ForeignKey("assets.id"), nullable=False, index=True)
    meta = Column(JSON, default=dict)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="user_metas")
    asset = relationship("Asset", back_populates="user_metas")

    __table_args__ = (
        UniqueConstraint("user_id", "asset_id", name="uq_user_meta"),
    )


class TaskAsset(Base):
    """Many-to-many: declares which assets a task reads from or writes to."""
    __tablename__ = "task_assets"

    task_id = Column(String(36), ForeignKey("tasks.id"), primary_key=True)
    asset_id = Column(String(36), ForeignKey("assets.id"), primary_key=True)
    role = Column(String(16), default="read")  # "read" | "write" | "context"

    task = relationship("Task", back_populates="asset_links")
    asset = relationship("Asset", back_populates="task_links")


class Interaction(Base):
    """
    Event log for all user interactions: reviews, questions, button taps, feedback.
    Replaces the question_log array in dsa_tracker.json.
    """
    __tablename__ = "interactions"

    id = Column(String(36), primary_key=True, default=_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    asset_id = Column(String(36), ForeignKey("assets.id"), nullable=True, index=True)
    record_key = Column(String(255), nullable=True)

    # "review" | "question" | "button_tap" | "feedback" | "hint" | "solution"
    event_type = Column(String(64), nullable=False)
    event_data = Column(JSON, default=dict)  # {"difficulty": "easy", "text": "…", "intent": "stuck"}

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="interactions")
    asset = relationship("Asset", back_populates="interactions")
