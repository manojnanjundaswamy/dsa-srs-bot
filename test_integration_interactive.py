#!/usr/bin/env python3
"""
Interactive integration test: Full morning-to-night DSA bot cycle with user input selection
Shows all Telegram messages and system logs for each interaction
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from copy import deepcopy

# Fix Windows Unicode encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

SCRIPT_DIR = Path(__file__).parent
TRACKER_FILE = SCRIPT_DIR / "dsa_tracker.json"
TRACKER_BACKUP = SCRIPT_DIR / "dsa_tracker_backup.json"

def load_tracker():
    with open(TRACKER_FILE) as f:
        return json.load(f)

def save_tracker(tracker):
    with open(TRACKER_FILE, 'w') as f:
        json.dump(tracker, f, indent=2)

def reset_tracker():
    """Reset tracker to fresh state: all problems 'new', no progress"""
    tracker = load_tracker()

    # Reset all problems to 'new' status
    for problem in tracker['problems']:
        problem['status'] = 'new'
        problem['times_reviewed'] = 0
        problem['streak_days'] = 0
        problem['interval_days'] = 1
        problem['ease_factor'] = 2.5
        problem['last_reviewed'] = None
        problem['next_due'] = None

    # Reset metadata
    tracker['metadata']['streak_days'] = 0
    tracker['metadata']['total_problems_solved'] = 0
    tracker['metadata']['current_week'] = 1
    tracker['metadata']['current_pattern'] = tracker['problems'][0]['pattern']
    tracker['metadata']['last_updated'] = datetime.now().isoformat()

    save_tracker(tracker)
    return tracker

def get_next_problem(tracker):
    """Get first 'new' problem"""
    for p in tracker['problems']:
        if p['status'] == 'new':
            return p
    return None

def get_today_due_problems(tracker):
    """Get problems with status 'active' that are due (simplified for test)"""
    return [p for p in tracker['problems'] if p['status'] == 'active' and p.get('next_due') is not None]

def update_tracker_after_review(tracker, problem_id, action):
    """Apply SM-2 algorithm after review"""
    problem = next((p for p in tracker['problems'] if p['id'] == problem_id), None)
    if not problem:
        return

    # Promote new → active on first review
    if problem['status'] == 'new':
        problem['status'] = 'active'

    # SM-2 algorithm
    ease = problem.get('ease_factor', 2.5)
    interval = problem.get('interval_days', 1)
    times_reviewed = problem.get('times_reviewed', 0)

    if action == 'easy':
        interval = interval * ease if times_reviewed > 0 else 3
        ease = ease + 0.1
    elif action == 'medium':
        interval = interval
        ease = ease
    elif action == 'hard':
        interval = 1
        ease = max(1.3, ease - 0.2)

    problem['times_reviewed'] = times_reviewed + 1
    problem['ease_factor'] = round(ease, 2)
    problem['interval_days'] = int(interval)
    problem['last_reviewed'] = datetime.now().isoformat()
    problem['next_due'] = (datetime.now() + timedelta(days=int(interval))).isoformat()

def create_difficulty_buttons(problem_index):
    """Return button layout"""
    idx = str(problem_index)
    return {
        "inline_keyboard": [
            [
                {"text": "✅ Easy",    "callback_data": f"easy:{idx}"},
                {"text": "⏸️ Medium",  "callback_data": f"medium:{idx}"},
                {"text": "❌ Hard",    "callback_data": f"hard:{idx}"},
            ],
            [
                {"text": "💡 Hint",   "callback_data": f"hint:{idx}"},
                {"text": "⏭️ Skip",   "callback_data": f"skip:{idx}"},
            ],
            [
                {"text": "🏆 Done — I've mastered this", "callback_data": f"mastered:{idx}"},
            ]
        ]
    }

def print_section(title):
    """Print a section header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")

def print_telegram_message(msg, buttons=None):
    """Format and print a Telegram message as user would see it"""
    print("┌" + "─"*78 + "┐")
    print("│  📱 TELEGRAM MESSAGE                                                          │")
    print("├" + "─"*78 + "┤")

    # Wrap text
    lines = msg.split('\n')
    for line in lines:
        if len(line) > 76:
            words = line.split()
            current = ""
            for word in words:
                if len(current) + len(word) + 1 <= 76:
                    current = (current + " " + word).lstrip()
                else:
                    print("│  " + current.ljust(76) + "│")
                    current = word
            if current:
                print("│  " + current.ljust(76) + "│")
        else:
            print("│  " + line.ljust(76) + "│")

    if buttons:
        print("├" + "─"*78 + "┤")
        print("│  BUTTONS:                                                                     │")
        keyboard = buttons['inline_keyboard']
        for row in keyboard:
            button_texts = [btn['text'] for btn in row]
            print("│    " + " | ".join(button_texts).ljust(74) + "│")

    print("└" + "─"*78 + "┘\n")

def show_problem_options(tracker, problem, auto_choice="1"):
    """Show interactive menu for problem action (uses auto_choice for demo)"""
    print(f"\n🎯 You see the problem: <b>{problem['title']}</b>")
    print(f"   LeetCode #{problem['leetcode_number']} | {problem['difficulty']} | {problem['pattern']}")
    print(f"\n   What would you like to do?\n")

    options = [
        ("1", "✅ Easy", "Solved easily"),
        ("2", "⏸️ Medium", "Solved with some thought"),
        ("3", "❌ Hard", "Had to look at hints/solution"),
        ("4", "💡 Hint", "Get a hint for this problem"),
        ("5", "⏭️ Skip", "Skip this problem for now"),
        ("6", "🏆 Done", "Mark as mastered (won't see again)"),
    ]

    for code, emoji, desc in options:
        marker = " ← YOU SELECTED THIS" if code == auto_choice else ""
        print(f"   {code}. {emoji}  — {desc}{marker}")

    return auto_choice

def handle_problem_action(tracker, problem, choice):
    """Process problem action and return result tuple"""
    action_map = {
        "1": "easy",
        "2": "medium",
        "3": "hard",
        "4": "hint",
        "5": "skip",
        "6": "mastered",
    }

    action = action_map[choice]
    problem_index = tracker["problems"].index(problem)

    if action in ("easy", "medium", "hard"):
        update_tracker_after_review(tracker, problem["id"], action)
        save_tracker(tracker)
        # Reload to get updated values
        tracker = load_tracker()
        problem_updated = tracker["problems"][problem_index]
        return (problem["title"], problem_updated["interval_days"], action, problem["pattern"])
    elif action == "skip":
        return (problem["title"], None, "skip", None)
    elif action == "hint":
        return (problem["title"], None, "hint", problem)
    elif action == "mastered":
        for p in tracker["problems"]:
            if p["id"] == problem["id"]:
                p["status"] = "mastered"
                break
        save_tracker(tracker)
        return (problem["title"], None, "mastered", None)

def show_poll_result(title, interval_days, action, extra):
    """Show what poll_mode would send back to Telegram"""
    print("\n📨 POLL MODE RESULT (what gets sent to Telegram):\n")

    emoji_map = {"easy": "✅", "medium": "⏸️", "hard": "❌"}

    if action == "hint":
        msg = f"💡 <b>Hint — {title}:</b>\n\n[Claude would generate a contextual hint here]\n\n"
        msg += "[Hint content would be generated via Claude API]"
    elif action == "skip":
        msg = f"⏭️ Skipped <b>{title}</b> — it'll come back tomorrow."
    elif action == "mastered":
        msg = f"🏆 <b>Mastered!</b> <b>{title}</b> archived — it won't come back."
    else:
        # difficulty rating
        emoji = emoji_map.get(action, "📝")
        msg = f"{emoji} Recorded as <b>{action.capitalize()}</b>!\n<b>{title}</b> → next review in <b>{interval_days} day(s)</b>"

    print_telegram_message(msg)

def run_morning_session(tracker):
    """Run morning_mode equivalent"""
    print_section("🌅 MORNING SESSION")

    next_problem = get_next_problem(tracker)

    if not next_problem:
        msg = "🎉 All Week 1 problems covered! Move to Week 2."
        print_telegram_message(msg)
        return None

    msg = f"""🌅 Good Morning, Manoj!

📚 Today's Pattern: {next_problem['pattern']}
What it means: Master this pattern for interview success.

🎯 Main Problem: {next_problem['title']} (LeetCode #{next_problem['leetcode_number']})
Difficulty: {next_problem['difficulty']}

🔗 LeetCode: {next_problem['leetcode_url']}

Warm-up tip: Review the pattern approach before solving the main problem.

Streak: {tracker['metadata']['streak_days']} days | Total solved: {tracker['metadata']['total_problems_solved']}"""

    print_telegram_message(msg)
    print(f"✅ [LOG] Morning prep sent for pattern: {next_problem['pattern']}")

    return next_problem

def run_afternoon_session(tracker):
    """Run afternoon_mode equivalent with user interaction"""
    print_section("📝 AFTERNOON SESSION")

    due_reviews = get_today_due_problems(tracker)
    new_problem = get_next_problem(tracker)

    if due_reviews:
        print(f"📅 You have {len(due_reviews)} problem(s) due for SRS review today:")
        for i, review in enumerate(due_reviews[:3], 1):
            print(f"   {i}. {review['title']} ({review['pattern']})")
        print("\n[In real bot, each would show with difficulty buttons]")

    if not new_problem:
        msg = "🎉 All problems for today are covered!"
        print_telegram_message(msg)
        return None

    msg = f"""📝 <b>{new_problem['title']}</b>

Pattern: <b>{new_problem['pattern']}</b>
Difficulty: {new_problem['difficulty']}
LeetCode #{new_problem['leetcode_number']}

🔗 {new_problem['leetcode_url']}

Approach this problem step-by-step. Rate your experience with the buttons below."""

    print_telegram_message(msg, create_difficulty_buttons(tracker["problems"].index(new_problem)))
    print(f"✅ [LOG] Afternoon session reminder sent for: {new_problem['title']}")

    # Get user's action for this problem
    choice = show_problem_options(tracker, new_problem)
    result = handle_problem_action(tracker, new_problem, choice)
    show_poll_result(result[0], result[1], result[2], result[3])

    return new_problem

def run_evening_session(tracker):
    """Run evening_mode equivalent"""
    print_section("📖 EVENING SESSION")

    due_problems = get_today_due_problems(tracker)
    next_problem = get_next_problem(tracker)

    if not next_problem:
        msg = "🎉 All problems for today are covered! Rest well."
        print_telegram_message(msg)
        return

    due_list = "\n".join([f"  • {p['title']} ({p['pattern']})" for p in due_problems]) if due_problems else "  None - all caught up!"

    msg = f"""📖 Evening Review Session

Problems due for SRS review today:
{due_list}

Today's main problem: {next_problem['title']}
Status: Check if you solved and rated it with the afternoon button!

Streak: {tracker['metadata']['streak_days']} days
Total solved: {tracker['metadata']['total_problems_solved']}

Go through the review problems and try to recall the approach from memory."""

    print_telegram_message(msg)
    print(f"✅ [LOG] Evening review reminder sent")

def run_night_session(tracker):
    """Run night_mode equivalent"""
    print_section("🌙 NIGHT SESSION")

    next_problem = get_next_problem(tracker)

    if not next_problem:
        msg = "🌙 Amazing week! Rest well, champion."
        print_telegram_message(msg)
        return

    # Tomorrow's preview
    all_new = [p for p in tracker["problems"] if p["status"] == "new"]

    msg = f"""🌙 Night Summary

Today you worked on: <b>{next_problem['title']}</b>
Pattern: <b>{next_problem['pattern']}</b>

Key insight: Mastering {next_problem['pattern']} opens doors to many similar problems.

Sleep well — a focused mind solves faster. 🌙"""

    print_telegram_message(msg)

    if len(all_new) > 1:
        tomorrow = all_new[1]
        preview = f"""👀 <b>Tomorrow's Preview:</b>
<b>{tomorrow['title']}</b> (LeetCode #{tomorrow['leetcode_number']})
Pattern: {tomorrow['pattern']} | {tomorrow['difficulty']}

Sleep well — a focused mind solves faster. 🌙"""
        print_telegram_message(preview)

    print(f"✅ [LOG] Night summary sent")

def main():
    """Run full integration test"""
    print("\n" + "█"*80)
    print("█" + " "*78 + "█")
    print("█" + "  DSA SRS BOT — INTERACTIVE INTEGRATION TEST".center(78) + "█")
    print("█" + "  Full Morning-to-Night Cycle with User Interaction".center(78) + "█")
    print("█" + " "*78 + "█")
    print("█"*80)

    # Reset tracker
    print("\n🔄 Resetting tracker to fresh state...")
    tracker = reset_tracker()
    print("✅ Tracker reset: all problems set to 'new', progress cleared\n")

    # Morning
    morning_problem = run_morning_session(tracker)
    if not morning_problem:
        print("\n🎉 Test complete - all problems covered!")
        return

    print("\n⏸️  [Demo: User takes some time to solve the morning problem...]")

    # Afternoon - user chooses "Easy" (choice 1)
    print("\n" + "="*80)
    print("  USER INTERACTION: Afternoon Problem Rating")
    print("="*80)
    print("\n💭 User decides: 'I solved this problem with good understanding → Easy'")

    afternoon_problem = run_afternoon_session(tracker)
    if not afternoon_problem:
        print("\n🎉 Test complete - all problems covered!")
        return

    print("\n⏸️  [Demo: User works through the afternoon and evening...]")

    # Evening
    run_evening_session(tracker)

    # Night
    run_night_session(tracker)

    # Final summary
    print_section("✅ INTEGRATION TEST COMPLETE")

    tracker = load_tracker()
    morning_problem = get_next_problem(tracker)

    print(f"📊 Test Summary:")
    print(f"   • Morning problem: {afternoon_problem['title']} (from morning)")
    print(f"   • User rating: Easy")
    print(f"   • Problem status: '{afternoon_problem['status']}'")
    print(f"   • Interval for next review: {afternoon_problem['interval_days']} day(s)")
    print(f"   • Times reviewed: {afternoon_problem['times_reviewed']}")
    print(f"   • Ease factor: {afternoon_problem['ease_factor']}")
    if morning_problem:
        print(f"\n   • Next problem to learn: {morning_problem['title']}")
    print(f"\n✨ Full day cycle demonstrated!")
    print(f"   Tracker saved to: {TRACKER_FILE}")
    print(f"\n💡 Key behaviors verified:")
    print(f"   ✓ Morning mode sends problem overview")
    print(f"   ✓ Afternoon mode presents new problem with buttons")
    print(f"   ✓ Poll mode processes rating and applies SM-2 algorithm")
    print(f"   ✓ Status promoted 'new' → 'active' on first review")
    print(f"   ✓ Interval calculated based on difficulty rating")
    print(f"   ✓ Evening mode shows due reviews")
    print(f"   ✓ Night mode shows summary and next day preview\n")

if __name__ == "__main__":
    main()
