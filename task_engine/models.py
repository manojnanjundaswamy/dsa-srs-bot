import uuid
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.types import JSON
from sqlalchemy.orm import relationship
from task_engine.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class Task(Base):
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True, default=_uuid)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")

    # Trigger type: "cron" | "interval" | "event" | "manual"
    type = Column(String(32), nullable=False)

    # Trigger configuration:
    #   cron:     {"cron": "0 7 * * *", "timezone": "Asia/Kolkata"}
    #   interval: {"interval_seconds": 10}
    #   event:    {"event_key": "some_key"}
    #   manual:   {}
    trigger_config = Column(JSON, default=dict)

    # Python code stored as text; executed via exec() at runtime
    script = Column(Text, nullable=False)

    # JSON dict injected as `args` variable inside exec context
    script_args = Column(JSON, default=dict)

    # Natural language prompt that generated the script (for reference/regeneration)
    prompt = Column(Text, default="")

    enabled = Column(Boolean, default=True, index=True)

    # Set when this task was duplicated from another
    parent_task_id = Column(String(36), ForeignKey("tasks.id"), nullable=True)

    # Denormalized from the last TaskRun — updated after every execution
    last_run_at = Column(DateTime, nullable=True)
    last_run_status = Column(String(16), nullable=True)  # "success" | "failed"

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    runs = relationship("TaskRun", back_populates="task", cascade="all, delete-orphan")


class TaskRun(Base):
    __tablename__ = "task_runs"

    id = Column(String(36), primary_key=True, default=_uuid)
    task_id = Column(String(36), ForeignKey("tasks.id"), nullable=False, index=True)

    # How the run was triggered
    triggered_by = Column(String(32), nullable=False)  # "scheduler" | "event" | "manual"

    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # "running" | "success" | "failed"
    status = Column(String(16), default="running")

    output = Column(Text, default="")
    error = Column(Text, nullable=True)

    task = relationship("Task", back_populates="runs")


class Asset(Base):
    __tablename__ = "assets"

    id = Column(String(36), primary_key=True, default=_uuid)
    name = Column(String(255), nullable=False)
    type = Column(String(64))   # "dsa_problems" | "user_context" | custom
    data = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
