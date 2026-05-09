"""
Task executor: runs a task's script via exec() with full bot context injected.

The context gives scripts access to all reminder_bot functions, config values,
and standard library modules — no imports needed inside the script itself.
"""

import json
import sys
import time
import traceback
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

# Add the project root to sys.path so reminder_bot can be imported
_PROJECT_ROOT = Path(__file__).parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from task_engine.models import Task, TaskRun


def _build_context(task: Task, event_data: Optional[dict] = None) -> dict:
    """Build the exec() globals dict for a task script."""
    import requests

    # Import reminder_bot lazily so logger is initialized by the time we use it
    try:
        import reminder_bot as bot
        # Ensure reminder_bot logger is set up (it may not be if called outside CLI)
        if bot.logger is None:
            bot.setup_logging("task_engine")
    except Exception as exc:
        raise RuntimeError(f"Could not import reminder_bot: {exc}") from exc

    output: list[str] = []

    ctx = {
        # ── All reminder_bot functions ──────────────────────────────────────
        "morning_mode":              bot.morning_mode,
        "afternoon_mode":            bot.afternoon_mode,
        "evening_mode":              bot.evening_mode,
        "night_mode":                bot.night_mode,
        "poll_mode":                 bot.poll_mode,
        "send_telegram_message":     bot.send_telegram_message,
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
        # ── Output capture (replaces print inside scripts) ─────────────────
        "print":     lambda *a, **_: output.append(" ".join(str(x) for x in a)),
        "_output":   output,  # executor reads this after exec()
    }
    return ctx


def run_task(task: Task, db: Session, triggered_by: str = "manual",
             event_data: Optional[dict] = None) -> TaskRun:
    """
    Execute a task's script and record the run in TaskRun.

    Returns the completed TaskRun row (status = "success" | "failed").
    """
    run = TaskRun(
        task_id=task.id,
        triggered_by=triggered_by,
        status="running",
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    ctx = _build_context(task, event_data)
    output_lines: list[str] = ctx["_output"]
    error_text: Optional[str] = None

    try:
        exec(task.script, ctx)  # noqa: S102
        run.status = "success"
    except Exception:
        run.status = "failed"
        error_text = traceback.format_exc()

    run.output = "\n".join(output_lines)
    run.error = error_text
    run.completed_at = datetime.utcnow()

    # Denormalize last run info onto the task for quick dashboard reads
    task.last_run_at = datetime.utcnow()
    task.last_run_status = run.status

    db.commit()
    db.refresh(run)
    return run
