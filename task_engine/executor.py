"""
Task executor: runs a task's script via exec() with full bot context injected.

The context gives scripts access to all reminder_bot functions, config values,
standard library modules, and DB-native asset helpers — no imports needed.

Structured execution events are emitted throughout and stored on TaskRun.events.
"""

import json
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

# Add the project root to sys.path so reminder_bot can be imported
_PROJECT_ROOT = Path(__file__).parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from task_engine.models import Task, TaskRun


# ── Event emitter ─────────────────────────────────────────────────────────────

class EventEmitter:
    """
    Collects structured execution events.
    Each event: {t, type, msg, level, ms?}
      t     = ms since task started
      type  = start | end | print | step | api_call | error
      msg   = human-readable description
      level = info | warn | error
      ms    = duration in ms (api_call events only)
    """

    def __init__(self, start_ns: int):
        self._start_ns = start_ns
        self.events: List[Dict[str, Any]] = []
        self.output_lines: List[str] = []

    def _t(self) -> int:
        return (time.perf_counter_ns() - self._start_ns) // 1_000_000

    def emit(self, type: str, msg: str, level: str = "info", **extra) -> None:
        ev: Dict[str, Any] = {"t": self._t(), "type": type, "msg": msg, "level": level}
        ev.update(extra)
        self.events.append(ev)

    def capture_print(self, *args, **_) -> None:
        text = " ".join(str(a) for a in args)
        self.output_lines.append(text)
        self.emit("print", text, level="info")

    def api_call(self, service: str, fn, *args, **kwargs):
        """Wrap an API-calling function with timing."""
        t0 = time.perf_counter_ns()
        self.emit("api_call", f"{service} → starting", level="info")
        try:
            result = fn(*args, **kwargs)
            ms = (time.perf_counter_ns() - t0) // 1_000_000
            self.emit("api_call", f"{service} → done", level="info", ms=ms)
            return result
        except Exception as e:
            ms = (time.perf_counter_ns() - t0) // 1_000_000
            self.emit("api_call", f"{service} → error: {e}", level="error", ms=ms)
            raise

    def wrap_telegram(self, original_fn):
        def _wrapped(text, **kwargs):
            return self.api_call("Telegram sendMessage", original_fn, text, **kwargs)
        return _wrapped

    def wrap_morning(self, original_fn):
        def _wrapped():
            self.emit("step", "Calling morning_mode()", level="info")
            return self.api_call("morning_mode", original_fn)
        return _wrapped

    def wrap_afternoon(self, original_fn):
        def _wrapped():
            self.emit("step", "Calling afternoon_mode()", level="info")
            return self.api_call("afternoon_mode", original_fn)
        return _wrapped

    def wrap_evening(self, original_fn):
        def _wrapped():
            self.emit("step", "Calling evening_mode()", level="info")
            return self.api_call("evening_mode", original_fn)
        return _wrapped

    def wrap_night(self, original_fn):
        def _wrapped():
            self.emit("step", "Calling night_mode()", level="info")
            return self.api_call("night_mode", original_fn)
        return _wrapped

    def wrap_poll(self, original_fn):
        def _wrapped():
            self.emit("step", "Calling poll_mode()", level="info")
            return self.api_call("poll_mode", original_fn)
        return _wrapped


# ── Context builder ───────────────────────────────────────────────────────────

def _build_context(task: Task, emitter: EventEmitter,
                   event_data: Optional[dict] = None,
                   db: Optional[Session] = None) -> dict:
    """Build the exec() globals dict for a task script."""
    import requests
    from task_engine.asset_helpers import build_asset_context

    try:
        import reminder_bot as bot
        if bot.logger is None:
            bot.setup_logging("task_engine")
    except Exception as exc:
        raise RuntimeError(f"Could not import reminder_bot: {exc}") from exc

    ctx: Dict[str, Any] = {
        # ── Wrapped bot functions (emit events) ────────────────────────────
        "morning_mode":              emitter.wrap_morning(bot.morning_mode),
        "afternoon_mode":            emitter.wrap_afternoon(bot.afternoon_mode),
        "evening_mode":              emitter.wrap_evening(bot.evening_mode),
        "night_mode":                emitter.wrap_night(bot.night_mode),
        "poll_mode":                 emitter.wrap_poll(bot.poll_mode),
        "send_telegram_message":     emitter.wrap_telegram(bot.send_telegram_message),
        # ── Unwrapped bot functions ────────────────────────────────────────
        "load_tracker":              bot.load_tracker,
        "save_tracker":              bot.save_tracker,
        "get_next_problem":          bot.get_next_problem,
        "get_today_due_problems":    bot.get_today_due_problems,
        "get_learning_stats":        bot.get_learning_stats,
        "analyze_weak_areas":        bot.analyze_weak_areas,
        "generate_hint_message":     bot.generate_hint_message,
        "generate_solution_preview": bot.generate_solution_preview,
        "generate_afternoon_message": bot.generate_afternoon_message,
        "handle_text_message":       bot.handle_text_message,
        "handle_stuck_message":      bot.handle_stuck_message,
        "detect_intent":             bot.detect_intent,
        "update_tracker_after_review": bot.update_tracker_after_review,
        "check_pattern_completion":  bot.check_pattern_completion,
        "create_adaptive_buttons":   bot.create_adaptive_buttons,
        "create_followup_buttons":   bot.create_followup_buttons,
        "PATTERN_EXPLANATIONS":      bot.PATTERN_EXPLANATIONS,
        # ── Config ─────────────────────────────────────────────────────────
        "CLAUDE_API_KEY":  bot.CLAUDE_API_KEY,
        "BOT_TOKEN":       bot.BOT_TOKEN,
        "CHAT_ID":         bot.CHAT_ID,
        "SCRIPT_DIR":      bot.SCRIPT_DIR,
        # ── Standard library ───────────────────────────────────────────────
        "datetime":  datetime,
        "requests":  requests,
        "time":      time,
        "json":      json,
        "Path":      Path,
        "logger":    bot.logger,
        # ── Task-specific ──────────────────────────────────────────────────
        "args":      task.script_args or {},
        "task_id":   task.id,
        "task_name": task.name,
        "event":     event_data or {},
        # ── Emit a custom step event from script ───────────────────────────
        "emit":      emitter.emit,
        # ── Output capture ─────────────────────────────────────────────────
        "print":     emitter.capture_print,
    }

    if db is not None:
        ctx.update(build_asset_context(db))

    return ctx


# ── Main run_task function ────────────────────────────────────────────────────

def run_task(task: Task, db: Session, triggered_by: str = "manual",
             event_data: Optional[dict] = None) -> TaskRun:
    """
    Execute a task's script and record the run in TaskRun.
    Returns the completed TaskRun row (status = 'success' | 'failed').
    """
    start_ns = time.perf_counter_ns()
    emitter = EventEmitter(start_ns)

    run = TaskRun(
        task_id=task.id,
        triggered_by=triggered_by,
        status="running",
        events=[],
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    emitter.emit("start", f"Task '{task.name}' started", level="info")

    ctx = _build_context(task, emitter, event_data=event_data, db=db)
    error_text: Optional[str] = None

    try:
        exec(task.script, ctx)  # noqa: S102
        run.status = "success"
        emitter.emit("end", "Task completed successfully", level="info")
    except Exception:
        run.status = "failed"
        error_text = traceback.format_exc()
        emitter.emit("error", error_text.splitlines()[-1], level="error")

    run.output = "\n".join(emitter.output_lines)
    run.error = error_text
    run.events = emitter.events
    run.completed_at = datetime.utcnow()

    # Denormalize last run info onto the task
    task.last_run_at = datetime.utcnow()
    task.last_run_status = run.status

    db.commit()
    db.refresh(run)
    return run
