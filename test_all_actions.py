#!/usr/bin/env python3
"""
Comprehensive demo showing all 6 button actions: Easy, Medium, Hard, Skip, Hint, Mastered
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Fix Windows Unicode encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

SCRIPT_DIR = Path(__file__).parent
TRACKER_FILE = SCRIPT_DIR / "dsa_tracker.json"

def load_tracker():
    with open(TRACKER_FILE) as f:
        return json.load(f)

def save_tracker(tracker):
    with open(TRACKER_FILE, 'w') as f:
        json.dump(tracker, f, indent=2)

def reset_tracker():
    """Reset tracker to fresh state"""
    tracker = load_tracker()
    for problem in tracker['problems']:
        problem['status'] = 'new'
        problem['times_reviewed'] = 0
        problem['interval_days'] = 1
        problem['ease_factor'] = 2.5
        problem['last_reviewed'] = None
        problem['next_due'] = None

    tracker['metadata']['streak_days'] = 0
    tracker['metadata']['total_problems_solved'] = 0
    tracker['metadata']['last_updated'] = datetime.now().isoformat()

    save_tracker(tracker)
    return tracker

def update_tracker_after_review(tracker, problem_id, action):
    """Apply SM-2 algorithm"""
    problem = next((p for p in tracker['problems'] if p['id'] == problem_id), None)
    if not problem:
        return

    if problem['status'] == 'new':
        problem['status'] = 'active'

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

def print_telegram_msg(title, text):
    """Format Telegram message display"""
    print("┌" + "─"*78 + "┐")
    print("│  " + f"📱 {title}".ljust(76) + "│")
    print("├" + "─"*78 + "┤")
    lines = text.split('\n')
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
    print("└" + "─"*78 + "┘\n")

def demo_action(action_name, problem, choice, tracker):
    """Demo a single action"""
    problem_index = tracker['problems'].index(problem)

    print(f"\n{'='*80}")
    print(f"  DEMO: {action_name} Button")
    print(f"{'='*80}\n")

    print(f"🎯 Problem: {problem['title']}")
    print(f"   LeetCode #{problem['leetcode_number']} | {problem['difficulty']} | {problem['pattern']}\n")

    # Show the telegram message with buttons
    msg = f"📝 <b>{problem['title']}</b>\n\nPattern: <b>{problem['pattern']}</b>\nDifficulty: {problem['difficulty']}\n🔗 {problem['leetcode_url']}"
    print_telegram_msg("Problem Message (with buttons below)", msg)

    # Show buttons with selection
    print("BUTTONS:")
    buttons = [
        ("✅ Easy", "3 days"),
        ("⏸️ Medium", "same day"),
        ("❌ Hard", "reset to 1 day"),
        ("💡 Hint", "get Claude hint"),
        ("⏭️ Skip", "skip for now"),
        ("🏆 Done", "archive forever"),
    ]
    for i, (btn, desc) in enumerate(buttons, 1):
        marker = " ← USER TAPS THIS" if str(i) == choice else ""
        print(f"  {i}. {btn:30} ({desc}){marker}")

    print("\n" + "-"*80)
    print("TELEGRAM RESPONSE:\n")

    action_map = {
        "1": ("easy", "3"),
        "2": ("medium", "1"),
        "3": ("hard", "1"),
        "4": ("hint", None),
        "5": ("skip", None),
        "6": ("mastered", None),
    }

    action, days = action_map[choice]

    # Process the action
    if action in ("easy", "medium", "hard"):
        update_tracker_after_review(tracker, problem["id"], action)
        save_tracker(tracker)
        tracker = load_tracker()
        problem_updated = tracker["problems"][problem_index]
        days = problem_updated["interval_days"]
        emoji = {"easy": "✅", "medium": "⏸️", "hard": "❌"}[action]
        response = f"{emoji} Recorded as <b>{action.capitalize()}</b>!\n<b>{problem['title']}</b> → next review in <b>{days} day(s)</b>"
    elif action == "skip":
        response = f"⏭️ Skipped <b>{problem['title']}</b> — it'll come back tomorrow."
    elif action == "hint":
        response = f"💡 <b>Hint — {problem['title']}:</b>\n\n[Claude-generated hint would appear here]\n\nConsider the data structure that allows O(1) lookup..."
    elif action == "mastered":
        for p in tracker['problems']:
            if p['id'] == problem['id']:
                p['status'] = 'mastered'
                break
        save_tracker(tracker)
        response = f"🏆 <b>Mastered!</b> <b>{problem['title']}</b> archived — it won't come back."

    print_telegram_msg("Poll Mode Response", response)

    print(f"✅ [LOG] Action processed: {action} for {problem['title']}")
    if action in ("easy", "medium", "hard"):
        print(f"✅ [LOG] SM-2 updated: times_reviewed={problem_updated['times_reviewed']}, "
              f"ease_factor={problem_updated['ease_factor']}, "
              f"next_due={problem_updated['interval_days']}d")
    elif action == "mastered":
        print(f"✅ [LOG] Status changed: new → mastered")
        print(f"✅ [NOTE] Problem will NOT appear in future reviews")

def main():
    print("\n" + "█"*80)
    print("█" + " "*78 + "█")
    print("█" + "  DSA BOT — COMPREHENSIVE ACTION DEMO".center(78) + "█")
    print("█" + "  All 6 Button Types: Easy, Medium, Hard, Hint, Skip, Mastered".center(78) + "█")
    print("█" + " "*78 + "█")
    print("█"*80)

    # Reset
    print("\n🔄 Resetting tracker...")
    tracker = reset_tracker()
    print("✅ Tracker reset to fresh state\n")

    # Get first 6 problems for the demos
    problems = [p for p in tracker['problems'] if p['status'] == 'new'][:6]

    actions = [
        ("EASY Rating", "1"),
        ("MEDIUM Rating", "2"),
        ("HARD Rating", "3"),
        ("HINT Request", "4"),
        ("SKIP Problem", "5"),
        ("MASTERED (Archive)", "6"),
    ]

    for (action_name, choice), problem in zip(actions, problems):
        demo_action(action_name, problem, choice, tracker)
        tracker = load_tracker()  # Reload after each action

    # Final status
    print("\n" + "="*80)
    print("  📊 FINAL TRACKER STATE")
    print("="*80 + "\n")

    tracker = load_tracker()
    print("Problem Status Overview:\n")

    statuses = {}
    for p in tracker['problems']:
        status = p['status']
        statuses[status] = statuses.get(status, 0) + 1
        if status != 'new':
            print(f"  • {p['title']:40} → {status:12} | reviewed: {p['times_reviewed']:2}x | "
                  f"interval: {p['interval_days']:2}d | ease: {p['ease_factor']:.2f}")

    print(f"\nStatus Counts:")
    print(f"  • new:       {statuses.get('new', 0):3} problems")
    print(f"  • active:    {statuses.get('active', 0):3} problems (will be reviewed)")
    print(f"  • mastered:  {statuses.get('mastered', 0):3} problems (archived forever)")

    print("\n" + "="*80)
    print("✨ Demo complete! All button actions demonstrated.")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
