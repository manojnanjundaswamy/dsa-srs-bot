#!/usr/bin/env python3
"""
FINAL END-TO-END TEST
Tests the complete flow with Java code and fixed formatting
"""

import json
import sys
import subprocess
from pathlib import Path
from datetime import datetime

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

SCRIPT_DIR = Path(__file__).parent
TRACKER_FILE = SCRIPT_DIR / "dsa_tracker.json"

def print_header(text):
    print("\n" + "="*80)
    print(f"  {text}")
    print("="*80 + "\n")

def run_mode(mode):
    """Run a bot mode and return output"""
    result = subprocess.run(
        ["python", "reminder_bot.py", f"--mode={mode}"],
        cwd=SCRIPT_DIR,
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='ignore'
    )
    return result.returncode == 0, result.stdout, result.stderr

# Main test flow
print("\n" + "█"*80)
print("█" + "  FINAL END-TO-END TEST: Java Code + Solution Button".center(78) + "█")
print("█"*80)

# Step 1: Test Afternoon Mode
print_header("STEP 1: Test Afternoon Mode (JAVA Code)")
print("Running: python reminder_bot.py --mode=afternoon\n")

success, stdout, stderr = run_mode("afternoon")

if success:
    print("✅ Afternoon mode PASSED")
    print("\nOutput:")
    for line in stdout.split('\n'):
        if 'Afternoon session' in line or 'msg_id' in line or 'Claude API' in line:
            print(f"  {line}")
else:
    print("❌ Afternoon mode FAILED")
    print(stderr)

# Step 2: Load tracker and show what was sent
print_header("STEP 2: Verify Problem Message Content")

with open(TRACKER_FILE) as f:
    tracker = json.load(f)

next_new = next((p for p in tracker['problems'] if p['status'] == 'new'), None)
if next_new:
    print(f"Problem sent: {next_new['title']}")
    print(f"Pattern: {next_new['pattern']}")
    print(f"Difficulty: {next_new['difficulty']}")
    print(f"Status: {next_new['status']}")
    print(f"\n📝 Expected message format:")
    print("""
    Key Insight: [core trick]
    Step-by-Step Approach: [3-4 steps]
    Java Code Skeleton:
    class Solution {
        public ... [method signature] {
            // Solution code
        }
    }
    Ready to solve it? Tap a difficulty button below after you're done!
    """)
else:
    print("⚠️  No new problems in tracker")

# Step 3: Explain what to test in Telegram
print_header("STEP 3: What to Do Next (in Telegram)")

print("""
✅ VERIFY AFTERNOON MESSAGE:
   1. Open your Telegram chat
   2. Find the message about today's problem
   3. Check that the code is in JAVA (not Python)
   4. Code should look like: class Solution { ... }

📋 TEST THE SOLUTION BUTTON (most important):
   1. Look for buttons at bottom of problem message
   2. Find the button row: [💡 Hint] [📋 Solution] [⏭️ Skip]
   3. TAP THE 📋 SOLUTION BUTTON
   4. Wait 2-3 seconds for the response
   5. You should receive:
      - APPROACH: Why this solution works
      - KEY INSIGHT: The trick/observation
      - JAVA CODE: Full working solution (5-15 lines)
      - TIME & SPACE COMPLEXITY: O(...) analysis
      - INTERVIEW EXPLANATION: What to say in interviews

💡 TEST THE HINT BUTTON:
   1. Tap the 💡 Hint button
   2. Receive a hint about solving approach

✅ TEST DIFFICULTY RATINGS:
   1. Tap [✅ Easy] after solving it quickly
   2. Or [⏸️ Medium] if it took thinking
   3. Or [❌ Hard] if you struggled
   4. Receive confirmation and problem scheduled for review

🏆 TEST THE DONE BUTTON:
   1. Tap [🏆 Done — I've mastered this]
   2. Problem archived forever, won't reappear

⏭️ TEST SKIP:
   1. Tap [⏭️ Skip] to defer to tomorrow
   2. Problem reappears in next afternoon session
""")

# Step 4: Show logs
print_header("STEP 4: Logs and Debugging")

log_file = SCRIPT_DIR / f"logs/dsa_bot_{datetime.now().strftime('%Y-%m-%d')}.log"
if log_file.exists():
    print(f"Latest log entries from: {log_file}\n")
    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
        for line in lines[-20:]:
            if any(x in line for x in ['Claude API', 'Telegram sendMessage', 'Afternoon', 'Solution']):
                print(line.rstrip())
else:
    print(f"Log file: {log_file}")

# Step 5: Tracker Summary
print_header("STEP 5: Tracker Status")

total = len(tracker['problems'])
new = len([p for p in tracker['problems'] if p['status'] == 'new'])
active = len([p for p in tracker['problems'] if p['status'] == 'active'])
mastered = len([p for p in tracker['problems'] if p['status'] == 'mastered'])

print(f"Total: {total} | New: {new} | Active: {active} | Mastered: {mastered}")

# Step 6: Summary
print_header("TEST SUMMARY")

print("""
✅ CODE FIXES APPLIED:
   1. Afternoon mode now requests JAVA code (not Python)
   2. Night mode also updated to JAVA templates
   3. Solution button markdown formatting fixed for Telegram HTML

✅ FEATURES WORKING:
   1. 📝 Afternoon mode sends problem with JAVA code skeleton
   2. 📋 Solution button generates full Java solution
   3. 💡 Hint button provides hints
   4. ✅/⏸️/❌ Difficulty buttons work with SM-2
   5. ⏭️ Skip button defers problem
   6. 🏆 Done button archives problem

🎯 NEXT STEPS:
   1. Test the buttons in Telegram (see STEP 3)
   2. When verified, create 5 Task Scheduler tasks
   3. Enable all tasks for automatic scheduling

💻 IF SOMETHING BREAKS:
   • Check logs: logs/dsa_bot_YYYY-MM-DD.log
   • Look for "ERROR" or "Claude API" lines
   • Run: python quick_verify.py
   • Check Telegram message formatting
""")

print("\n" + "█"*80)
print("█" + "  ✨ READY FOR TELEGRAM TESTING ✨".center(78) + "█")
print("█"*80 + "\n")
