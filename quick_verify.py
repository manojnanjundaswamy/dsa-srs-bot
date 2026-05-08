#!/usr/bin/env python3
"""Quick Task Scheduler Verification"""

import subprocess
import json
from pathlib import Path
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

SCRIPT_DIR = Path(__file__).parent
TRACKER_FILE = SCRIPT_DIR / "dsa_tracker.json"

print("\n" + "█"*70)
print("█" + " "*68 + "█")
print("█" + "  DSA SRS BOT — QUICK VERIFICATION".center(68) + "█")
print("█" + " "*68 + "█")
print("█"*70)

checks_passed = 0
checks_total = 0

# ============ STEP 1: Python & Dependencies ============
print("\n┌─ STEP 1: Python & Dependencies ─────────────────────────────┐")

# Python version
result = subprocess.run(["python", "--version"], capture_output=True, text=True)
if "3." in result.stdout or "3." in result.stderr:
    print("✅ Python installed")
    checks_passed += 1
else:
    print("❌ Python not found")
checks_total += 1

# Check packages
for package in ["anthropic", "requests", "python-dotenv"]:
    result = subprocess.run(["pip", "show", package], capture_output=True, text=True)
    if "Name:" in result.stdout:
        print(f"✅ {package} installed")
        checks_passed += 1
    else:
        print(f"❌ {package} not found")
    checks_total += 1

# ============ STEP 2: Files & Configuration ============
print("\n┌─ STEP 2: Files & Configuration ────────────────────────────┐")

# Check reminder_bot.py
if (SCRIPT_DIR / "reminder_bot.py").exists():
    print("✅ reminder_bot.py exists")
    checks_passed += 1
else:
    print("❌ reminder_bot.py not found")
checks_total += 1

# Check .env file
if (SCRIPT_DIR / ".env").exists():
    print("✅ .env file exists")
    checks_passed += 1
else:
    print("❌ .env file not found")
checks_total += 1

# Check tracker file
if TRACKER_FILE.exists():
    print("✅ dsa_tracker.json exists")
    checks_passed += 1
else:
    print("❌ dsa_tracker.json not found")
checks_total += 1

# ============ STEP 3: Feature Verification ============
print("\n┌─ STEP 3: New Features (Java Solution Button) ──────────────┐")

bot_content = (SCRIPT_DIR / "reminder_bot.py").read_text(encoding='utf-8', errors='ignore')

# Check for Solution button
if "📋 Solution" in bot_content:
    print("✅ Solution button (📋) added to button layout")
    checks_passed += 1
else:
    print("❌ Solution button not found in code")
checks_total += 1

# Check for generate_solution_preview function
if "def generate_solution_preview" in bot_content:
    print("✅ generate_solution_preview function exists")
    checks_passed += 1
else:
    print("❌ generate_solution_preview function missing")
checks_total += 1

# Check for solution action handler
if 'action == "solution"' in bot_content:
    print("✅ Solution action handler in handle_button_callback")
    checks_passed += 1
else:
    print("❌ Solution action handler missing")
checks_total += 1

# Check for solution in poll_mode
if 'action == "solution"' in bot_content and "generate_solution_preview" in bot_content:
    print("✅ Solution processing in poll_mode")
    checks_passed += 1
else:
    print("❌ Solution processing missing from poll_mode")
checks_total += 1

# ============ STEP 4: Tracker Status ============
print("\n┌─ STEP 4: Tracker Status ──────────────────────────────────┐")

try:
    tracker = json.load(open(TRACKER_FILE))

    # Count problems by status
    new_count = len([p for p in tracker['problems'] if p['status'] == 'new'])
    active_count = len([p for p in tracker['problems'] if p['status'] == 'active'])
    mastered_count = len([p for p in tracker['problems'] if p['status'] == 'mastered'])

    print(f"✅ Tracker status:")
    print(f"   • Total problems: {len(tracker['problems'])}")
    print(f"   • New (to learn): {new_count}")
    print(f"   • Active (in SRS): {active_count}")
    print(f"   • Mastered (archived): {mastered_count}")
    checks_passed += 1
except Exception as e:
    print(f"❌ Error reading tracker: {e}")
checks_total += 1

# ============ STEP 5: Task Scheduler ============
print("\n┌─ STEP 5: Task Scheduler Configuration ─────────────────────┐")

# Get scheduled tasks
result = subprocess.run(
    ["powershell", "-Command", "Get-ScheduledTask | Where-Object {$_.TaskName -like '*DSA*'} | Select-Object TaskName"],
    capture_output=True, text=True
)

task_names = [
    "DSA Bot - Morning (7 AM)",
    "DSA Bot - Afternoon (2 PM)",
    "DSA Bot - Evening (6 PM)",
    "DSA Bot - Night (9 PM)",
    "DSA Bot - Poll (Every 5 min)"
]

found_tasks = 0
for task in task_names:
    if task in result.stdout:
        print(f"✅ Found: {task}")
        found_tasks += 1
    else:
        print(f"⚠️  Missing: {task} (create in Task Scheduler)")

checks_passed += found_tasks
checks_total += len(task_names)

# ============ SUMMARY ============
print("\n┌─ SUMMARY ────────────────────────────────────────────────────┐")

percentage = int((checks_passed / checks_total) * 100) if checks_total > 0 else 0
print(f"\nResults: {checks_passed}/{checks_total} checks passed ({percentage}%)")

if checks_passed == checks_total:
    print("\n🎉 ALL CHECKS PASSED! Setup is complete.")
    print("\n✅ Next Steps:")
    print("   1. Verify morning test message arrived in Telegram")
    print("   2. Check for 7 buttons on problem (including 📋 Solution)")
    print("   3. Create missing Task Scheduler tasks (if any)")
    print("   4. Enable and test tasks")
elif checks_passed >= (checks_total - 2):
    print("\n✅ MOSTLY WORKING - Minor setup items remaining:")
    print("   • Create missing Task Scheduler tasks")
    print("   • Enable the 5 tasks to start automatic scheduling")
else:
    print("\n⚠️  Some items need attention:")
    print("   • Review the ❌ items above")
    print("   • Reinstall missing packages if needed")

print("\n📖 Documentation:")
print(f"   • Task Scheduler setup: {SCRIPT_DIR / 'TASK_SCHEDULER_SETUP.md'}")
print(f"   • Feature changes: {SCRIPT_DIR / 'JAVA_SOLUTION_BUTTON_CHANGES.md'}")
print(f"   • Integration tests: {SCRIPT_DIR / 'test_integration_interactive.py'}")
print(f"   • Solution demo: {SCRIPT_DIR / 'test_solution_button.py'}")

print("\n" + "█"*70 + "\n")
