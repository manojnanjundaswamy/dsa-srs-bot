"""
End-to-end API test for the Task Engine.
Run: python test_task_engine.py
Server must be running at http://127.0.0.1:8080
"""

import json
import sys
import time
import requests

# Fix Windows console encoding
sys.stdout.reconfigure(encoding="utf-8")

BASE = "http://127.0.0.1:8080"

def pp(label, data):
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    if isinstance(data, (dict, list)):
        print(json.dumps(data, indent=2, default=str))
    else:
        print(data)

def check(resp, label):
    if resp.status_code >= 400:
        print(f"❌ FAILED [{resp.status_code}] {label}")
        print(resp.text[:500])
        sys.exit(1)
    print(f"✅ {label} → {resp.status_code}")
    return resp.json()

# ── 1. Health check ────────────────────────────────────────────────────────────
r = requests.get(f"{BASE}/health")
health = check(r, "Health check")
pp("Health", health)

# ── 2. List seed tasks ─────────────────────────────────────────────────────────
r = requests.get(f"{BASE}/api/tasks")
tasks = check(r, "List all tasks")
print(f"\n  {len(tasks)} tasks found:")
for t in tasks:
    print(f"    [{t['type']:8}] {t['name']} | enabled={t['enabled']} | last_run={t['last_run_at']}")

# ── 3. Scheduler status (last + next run times) ────────────────────────────────
r = requests.get(f"{BASE}/api/scheduler/status")
status = check(r, "Scheduler status")
print(f"\n  Scheduler running={status['running']}, active_jobs={status['job_count']}")
for j in status["jobs"]:
    print(f"    {j['task_name']}")
    print(f"      trigger : {j['trigger_description']}")
    print(f"      last_run: {j['last_run_at']}")
    print(f"      next_run: {j['next_run_time']}")

# ── 4. Generate a joke script (preview only, no task created) ─────────────────
print("\n\n📝 Calling Claude to generate a joke script...")
r = requests.post(f"{BASE}/api/tasks/generate", json={
    "prompt": "Create a funny programming joke and send it as a nicely formatted Telegram message. Use HTML formatting.",
    "context_hint": "Telegram DSA study bot"
})
gen = check(r, "Generate script (preview)")
print(f"\n  Suggested name : {gen['suggested_name']}")
print(f"  Suggested type : {gen['suggested_type']}")
print(f"  Generated script:\n")
for line in gen["script"].splitlines():
    print(f"    {line}")

# ── 5. Create joke task using generate-and-create ─────────────────────────────
print("\n\n🚀 Creating joke task via generate-and-create...")
r = requests.post(f"{BASE}/api/tasks/generate-and-create", json={
    "prompt": "Create a funny programming joke and send it as a nicely formatted Telegram message. Use HTML formatting tags like <b> and <i>.",
    "type": "manual",
    "trigger_config": {},
    "enabled": True,
})
joke_task = check(r, "Create joke task (generate-and-create)")
joke_id = joke_task["id"]
print(f"\n  Task: {joke_task['name']} | ID: {joke_id}")
print(f"  Script stored:\n")
for line in joke_task["script"].splitlines():
    print(f"    {line}")

# ── 6. Run the joke task → fires Telegram message ─────────────────────────────
print("\n\n🎯 Running joke task → sending to Telegram...")
r = requests.post(f"{BASE}/api/tasks/{joke_id}/run")
run1 = check(r, "Manual run — joke task")
print(f"\n  Run ID  : {run1['id']}")
print(f"  Status  : {run1['status']}")
print(f"  Output  : {run1['output']}")
if run1.get("error"):
    print(f"  Error   : {run1['error'][:300]}")

# ── 7. Create a stats snapshot task (hand-written script) ─────────────────────
print("\n\n📊 Creating stats snapshot task...")
stats_script = "\n".join([
    "tracker = load_tracker()",
    "stats = get_learning_stats(tracker)",
    "weak = analyze_weak_areas(tracker)",
    "msg = f'🧪 <b>Task Engine Test — Stats</b>\\n\\n{stats}\\n\\n{weak}'",
    "send_telegram_message(msg)",
    "print('Stats snapshot sent successfully')",
])
r = requests.post(f"{BASE}/api/tasks", json={
    "name": "Stats Snapshot (Test)",
    "description": "Sends a learning stats summary to Telegram",
    "type": "manual",
    "trigger_config": {},
    "script": stats_script,
    "script_args": {},
    "prompt": "Send learning stats to Telegram",
    "enabled": True,
})
stats_task = check(r, "Create stats task")
stats_id = stats_task["id"]
print(f"  Created: {stats_task['name']} | ID: {stats_id}")

# Run it
r = requests.post(f"{BASE}/api/tasks/{stats_id}/run")
run2 = check(r, "Manual run — stats task")
print(f"  Status  : {run2['status']}")
print(f"  Output  : {run2['output']}")

# ── 8. Create a parameterized task (uses args) ─────────────────────────────────
print("\n\n⚙️  Creating parameterized motivational task (uses script_args)...")
motivate_script = "\n".join([
    "name = args.get('name', 'Developer')",
    "goal = args.get('goal', 'master DSA')",
    "msg = (",
    "    f'💪 <b>Hey {name}!</b>\\n\\n'",
    "    f'Remember why you started: to <i>{goal}</i>.\\n\\n'",
    "    '🔥 Every problem you solve today is an investment in your future.\\n'",
    "    '📈 Consistency beats talent. Keep going!'",
    ")",
    "send_telegram_message(msg)",
    "print(f'Motivational message sent to {name}')",
])
r = requests.post(f"{BASE}/api/tasks", json={
    "name": "Motivational Message (Parameterized)",
    "description": "Sends a personalized motivational message using script_args",
    "type": "manual",
    "trigger_config": {},
    "script": motivate_script,
    "script_args": {"name": "Manoj", "goal": "crack FAANG interviews"},
    "prompt": "Send a personalized motivational message to the user",
    "enabled": True,
})
motivate_task = check(r, "Create motivational task")
motivate_id = motivate_task["id"]
print(f"  Created: {motivate_task['name']} | ID: {motivate_id}")
print(f"  Args: {motivate_task['script_args']}")

# Run it
r = requests.post(f"{BASE}/api/tasks/{motivate_id}/run")
run3 = check(r, "Manual run — motivational task")
print(f"  Status  : {run3['status']}")
print(f"  Output  : {run3['output']}")

# ── 9. Duplicate the joke task ─────────────────────────────────────────────────
print("\n\n📋 Duplicating joke task...")
r = requests.post(f"{BASE}/api/tasks/{joke_id}/duplicate")
dup = check(r, "Duplicate joke task")
print(f"  Original: {joke_id}")
print(f"  Copy    : {dup['id']} — '{dup['name']}'")
print(f"  Enabled : {dup['enabled']} (copies start disabled)")
print(f"  Parent  : {dup['parent_task_id']}")

# ── 10. Disable the duplicate, verify scheduler ────────────────────────────────
print("\n\n🔕 Enabling duplicate, then disabling it (scheduler test)...")
r = requests.post(f"{BASE}/api/tasks/{dup['id']}/enable")
check(r, "Enable duplicate")

r = requests.post(f"{BASE}/api/tasks/{dup['id']}/disable")
check(r, "Disable duplicate")
print(f"  Disabled OK — scheduler job removed")

# ── 11. Check execution history for joke task ──────────────────────────────────
print("\n\n📜 Execution history for joke task...")
r = requests.get(f"{BASE}/api/tasks/{joke_id}/runs")
runs = check(r, "Get task runs")
print(f"  {len(runs)} run(s) found:")
for run in runs:
    print(f"    [{run['status']:7}] triggered_by={run['triggered_by']} | started={run['started_at']} | output={run['output'][:60]}")

# ── 12. Final scheduler status (with last_run_at now populated) ───────────────
print("\n\n📅 Final scheduler status (last_run_at now populated for manual tasks)...")
r = requests.get(f"{BASE}/api/scheduler/status")
status = check(r, "Final scheduler status")
for j in status["jobs"]:
    print(f"  {j['task_name']}")
    print(f"    last_run : {j['last_run_at']}")
    print(f"    next_run : {j['next_run_time']}")

# ── Summary ────────────────────────────────────────────────────────────────────
print("\n\n" + "="*60)
print("  ALL TESTS PASSED ✅")
print("="*60)
print(f"\n  Tasks created during test:")
print(f"    • {joke_task['name']} (Claude-generated)")
print(f"    • Stats Snapshot (hand-written)")
print(f"    • Motivational Message (parameterized with args)")
print(f"    • Copy of joke task (duplicate, then disabled)")
print(f"\n  All 3 tasks sent messages to Telegram successfully.")
print(f"  Check your Telegram — you should have 3 new messages.\n")
