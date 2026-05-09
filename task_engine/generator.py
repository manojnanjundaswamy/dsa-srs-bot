"""
Claude-powered script generator.

Takes a natural language prompt and returns a Python script ready to be stored
in a Task.script field. The script has access to all reminder_bot functions
via the executor's injected context.
"""

from anthropic import Anthropic
from task_engine.config import CLAUDE_API_KEY

# Functions available in every script's execution context (shown to Claude)
_CONTEXT_REFERENCE = """
Available in every task script (no imports needed):
  Bot actions:
    morning_mode()            - send morning DSA session message
    afternoon_mode()          - send afternoon problem + buttons
    evening_mode()            - send evening review reminder
    night_mode()              - send night summary
    poll_mode()               - poll Telegram once for messages/buttons
    send_telegram_message(text, reply_markup=None)  - send any Telegram message
  Data:
    load_tracker()            - returns the dsa_tracker dict
    save_tracker(tracker)     - saves the tracker dict to disk
    get_next_problem(tracker) - returns the next unsolved problem dict
    get_today_due_problems(tracker) - returns list of problems due today
    get_learning_stats(tracker)     - returns formatted stats string
    analyze_weak_areas(tracker)     - returns weak areas string
    generate_hint_message(problem)  - returns hint string
    generate_solution_preview(problem) - returns solution string
    generate_afternoon_message(problem) - returns afternoon message string
  Config:
    CLAUDE_API_KEY, BOT_TOKEN, CHAT_ID
  Standard library:
    datetime, requests, time, json, Path, logger
  Task inputs:
    args   - dict from task.script_args (user-defined at task creation)
    event  - dict from webhook payload (for event-type tasks)
    task_id, task_name
  Output:
    Use print() to capture output in the TaskRun log.
"""

_SYSTEM_PROMPT = f"""You are a Python script generator for a Telegram DSA study bot.

Write a concise Python script that accomplishes what the user describes.
The script runs inside an exec() context — no imports needed, all functions below are pre-injected.

{_CONTEXT_REFERENCE}

Rules:
- Write ONLY the script body (no function/class definitions, no if __name__ == '__main__')
- Use pre-injected functions; do NOT import them
- Keep scripts short and focused (5-20 lines is typical)
- Use print() to capture meaningful output for logs
- If the task uses dynamic data, use args['key'] (args dict is always available)
- Never hardcode credentials; they are pre-injected

Also return a suggested task name (≤60 chars) and trigger type.
Respond in this EXACT format — no markdown fences:

NAME: <suggested task name>
TYPE: <cron|interval|event|manual>
TRIGGER: <cron expression like "0 9 * * 1" or interval_seconds like "3600" or "none">
SCRIPT:
<the python script>
"""


def generate_script(prompt: str, context_hint: str = "") -> dict:
    """
    Call Claude to generate a task script from a natural language prompt.

    Returns:
        {
            "script": str,
            "suggested_name": str,
            "suggested_type": str,        # cron | interval | event | manual
            "suggested_trigger": dict,    # ready for trigger_config field
        }
    """
    client = Anthropic(api_key=CLAUDE_API_KEY)

    user_msg = prompt
    if context_hint:
        user_msg = f"{prompt}\n\nContext: {context_hint}"

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=600,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )

    raw = response.content[0].text.strip()
    return _parse_response(raw)


def _parse_response(raw: str) -> dict:
    """Parse Claude's structured response into a dict."""
    lines = raw.splitlines()
    name = "Generated Task"
    task_type = "manual"
    trigger_raw = "none"
    script_lines: list[str] = []
    in_script = False

    for line in lines:
        if line.startswith("NAME:"):
            name = line.removeprefix("NAME:").strip()
        elif line.startswith("TYPE:"):
            task_type = line.removeprefix("TYPE:").strip().lower()
        elif line.startswith("TRIGGER:"):
            trigger_raw = line.removeprefix("TRIGGER:").strip()
        elif line.startswith("SCRIPT:"):
            in_script = True
        elif in_script:
            script_lines.append(line)

    script = "\n".join(script_lines).strip()

    # Build trigger_config
    trigger_config: dict = {}
    if task_type == "cron" and trigger_raw != "none":
        trigger_config = {"cron": trigger_raw, "timezone": "Asia/Kolkata"}
    elif task_type == "interval":
        try:
            trigger_config = {"interval_seconds": int(trigger_raw)}
        except ValueError:
            trigger_config = {"interval_seconds": 60}
    elif task_type == "event":
        trigger_config = {"event_key": trigger_raw if trigger_raw != "none" else "custom"}

    return {
        "script": script or "# TODO: fill in script body",
        "suggested_name": name[:60],
        "suggested_type": task_type,
        "suggested_trigger": trigger_config,
    }
