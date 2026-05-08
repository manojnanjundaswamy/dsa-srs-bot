#!/usr/bin/env python3
"""
End-to-End Test: Afternoon Mode → Solution Button → Poll Mode Response
Tests the complete flow of sending a problem with buttons and processing a button tap.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
import subprocess

# Fix Windows Unicode encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

SCRIPT_DIR = Path(__file__).parent
TRACKER_FILE = SCRIPT_DIR / "dsa_tracker.json"

def print_header(title):
    print("\n" + "█"*80)
    print("█" + title.center(78) + "█")
    print("█"*80 + "\n")

def print_section(title):
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")

print_header("E2E TEST: Afternoon Mode → Solution Button → Response")

# Step 1: Run afternoon mode
print_section("STEP 1: Run Afternoon Mode (should show Java code now)")
print("Running: python reminder_bot.py --mode afternoon\n")
print("This will send a problem message with 7 buttons to Telegram.")
print("Watch for the Java code skeleton in the message.\n")

result = subprocess.run(
    ["python", "reminder_bot.py", "--mode afternoon"],
    cwd=SCRIPT_DIR,
    capture_output=True,
    text=True,
    encoding='utf-8',
    errors='ignore'
)

print("STDOUT:")
print(result.stdout)
if result.stderr:
    print("\nSTDERR:")
    print(result.stderr)

if result.returncode == 0:
    print("\n✅ Afternoon mode executed successfully!")
else:
    print(f"\n❌ Afternoon mode failed with return code {result.returncode}")

# Step 2: Show instructions for manual testing
print_section("STEP 2: Manual Testing Instructions")

print("""
Now that the afternoon message has been sent to Telegram:

1. ✅ VERIFY MESSAGE CONTENT:
   • Open your Telegram chat
   • Look for the latest message about today's problem
   • Check that the code skeleton is in JAVA (not Python)
   • Should show: class Solution { ... }

2. 📋 TEST THE SOLUTION BUTTON:
   • Find the button row with: [💡 Hint] [📋 Solution] [⏭️ Skip]
   • Tap the 📋 Solution button
   • Wait 2-3 seconds for the response

3. ✨ VERIFY SOLUTION RESPONSE:
   • You should receive a message with:
     - APPROACH: Core idea
     - KEY INSIGHT: Interview trick
     - JAVA CODE: Full solution (5-15 lines)
     - TIME & SPACE COMPLEXITY: Both analyzed
     - INTERVIEW EXPLANATION: What to say

4. 💡 TEST THE HINT BUTTON:
   • Tap the 💡 Hint button on the original message
   • Should receive a shorter hint about the approach

5. ✅ TEST A DIFFICULTY RATING:
   • Tap one of: [✅ Easy] [⏸️ Medium] [❌ Hard]
   • Should receive confirmation like: "Easy solve recorded!"
   • Problem should reappear in SRS based on difficulty

6. 🏆 TEST THE DONE BUTTON:
   • Tap [🏆 Done — I've mastered this]
   • Should receive: "Mastered! <Problem> archived — it won't come back."
   • Problem removed from future review queue
""")

# Step 3: Show what to check in logs
print_section("STEP 3: Check Logs for API Calls")

log_file = SCRIPT_DIR / f"logs/dsa_bot_{datetime.now().strftime('%Y-%m-%d')}.log"
if log_file.exists():
    print(f"Log file: {log_file}\n")
    print("Last 30 lines of the log:")
    print("-" * 80)

    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
        for line in lines[-30:]:
            print(line.rstrip())

    print("\n" + "-" * 80)
else:
    print(f"⚠️  Log file not yet created: {log_file}")

# Step 4: Show tracker status
print_section("STEP 4: Tracker Status")

try:
    with open(TRACKER_FILE) as f:
        tracker = json.load(f)

    total = len(tracker['problems'])
    new = len([p for p in tracker['problems'] if p['status'] == 'new'])
    active = len([p for p in tracker['problems'] if p['status'] == 'active'])
    mastered = len([p for p in tracker['problems'] if p['status'] == 'mastered'])

    print(f"Total problems: {total}")
    print(f"  • New: {new}")
    print(f"  • Active (in SRS): {active}")
    print(f"  • Mastered (archived): {mastered}")

    # Show the first few active/new problems
    print("\nNext 3 problems to work on:")
    new_problems = [p for p in tracker['problems'] if p['status'] == 'new'][:3]
    for i, p in enumerate(new_problems, 1):
        print(f"  {i}. {p['title']} ({p['pattern']})")

except Exception as e:
    print(f"Error reading tracker: {e}")

# Step 5: Summary
print_section("TEST SUMMARY")

print("""
✅ CODE FIX APPLIED:
   • Afternoon mode now asks for JAVA code (not Python)
   • Night mode also updated to use JAVA templates

✅ FEATURES AVAILABLE:
   1. 📝 Problem with JAVA code skeleton (afternoon mode)
   2. 📋 Solution button → Full JAVA solution + interview explanation
   3. 💡 Hint button → Targeted hint from Claude
   4. ✅/⏸️/❌ Difficulty buttons → Record solve and schedule review
   5. ⏭️ Skip button → Defer to tomorrow
   6. 🏆 Done button → Archive problem forever

✨ NEXT STEPS:
   1. Test buttons in Telegram (follow instructions above)
   2. After confirming it works, create Task Scheduler tasks
   3. Enable all 5 tasks for automatic scheduling

📧 DEBUGGING:
   • Check logs in: logs/dsa_bot_YYYY-MM-DD.log
   • Look for "Claude API" lines showing token usage
   • Check for "ERROR" or "Exception" if something breaks
""")

print_header("E2E TEST READY - Test in Telegram Now")
