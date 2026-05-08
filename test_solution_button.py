#!/usr/bin/env python3
"""
Demo: New 📋 Solution Button with Java Code & Interview Explanation
Shows formatted solution ready for phone/tablet viewing
"""

import json
import sys
from pathlib import Path

# Fix Windows Unicode encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

SCRIPT_DIR = Path(__file__).parent
TRACKER_FILE = SCRIPT_DIR / "dsa_tracker.json"

def load_tracker():
    with open(TRACKER_FILE) as f:
        return json.load(f)

def print_section(title):
    """Print section header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")

def print_telegram_msg(title, text):
    """Format Telegram message with word wrapping"""
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

def demo_solution():
    """Show the Solution button and sample output"""

    print("\n" + "█"*80)
    print("█" + " "*78 + "█")
    print("█" + "  DSA BOT — NEW 📋 SOLUTION BUTTON DEMO".center(78) + "█")
    print("█" + "  Java Code + Interview Explanation".center(78) + "█")
    print("█" + " "*78 + "█")
    print("█"*80)

    # Get a problem
    tracker = load_tracker()
    problem = tracker['problems'][0]  # Contains Duplicate

    print_section("1️⃣  PROBLEM MESSAGE WITH NEW BUTTON")

    msg = f"""📝 <b>{problem['title']}</b>

Pattern: <b>{problem['pattern']}</b>
Difficulty: {problem['difficulty']}
LeetCode #{problem['leetcode_number']}

🔗 {problem['leetcode_url']}

Approach this problem step-by-step. Rate your experience with the buttons below."""

    print(msg)

    # Show buttons
    print("\nBUTTON LAYOUT (Updated with 📋 Solution):")
    buttons = [
        ("✅ Easy", "Record: Easy solve"),
        ("⏸️ Medium", "Record: Medium solve"),
        ("❌ Hard", "Record: Hard solve"),
        ("💡 Hint", "Get Claude hint"),
        ("📋 Solution", "See formatted Java + explanation ← NEW!"),
        ("⏭️ Skip", "Skip for now"),
        ("🏆 Done", "Archive forever"),
    ]

    for i, (btn, desc) in enumerate(buttons, 1):
        marker = " ◄ NEW BUTTON" if "Solution" in btn else ""
        print(f"  {i}. {btn:30} — {desc}{marker}")

    print_section("2️⃣  WHEN USER TAPS 📋 SOLUTION BUTTON")

    # Example solution response
    solution_text = f"""📋 Solution — {problem['title']}

## APPROACH
Use a hash set to track seen numbers. As you iterate through the array, check if each number exists in the set. If it does, we found a duplicate. If not, add it to the set and continue.

## KEY INSIGHT
Hash Set allows O(1) lookup — this is the interviewer's expected trick! They want to see you recognize the data structure choice.

## JAVA CODE
```java
class Solution {{
    public boolean containsDuplicate(int[] nums) {{
        Set<Integer> seen = new HashSet<>();
        for (int num : nums) {{
            if (seen.contains(num)) {{
                return true;
            }}
            seen.add(num);
        }}
        return false;
    }}
}}
```

## TIME & SPACE COMPLEXITY
- Time: O(n) — single pass through array, O(1) lookup per element
- Space: O(n) — worst case all unique numbers in set

## INTERVIEW EXPLANATION
When explaining in an interview:
1. Say: "I'll use a hash set to track seen values"
2. Mention: "This gives me O(1) lookup which is critical"
3. Explain: "Trade space for time — store numbers to achieve linear time"
"""

    print_telegram_msg("Poll Mode Response (Solution Tap)", solution_text)

    print_section("3️⃣  KEY FEATURES")

    features = [
        ("✅ Java Code", "Not Python — matches your DSA work"),
        ("✅ Compact Format", "Max 15 lines for mobile readability"),
        ("✅ Interview-Focused", "Explains WHAT to say in interviews"),
        ("✅ Complexity Analysis", "Time & Space both explained"),
        ("✅ Mobile-Friendly", "Formatted for phone/tablet viewing"),
        ("✅ Read-Only Action", "Doesn't change problem state or status"),
        ("✅ Works Everywhere", "Even on mastered problems"),
    ]

    for title, desc in features:
        print(f"{title:20} → {desc}")

    print_section("4️⃣  COMPLETE BUTTON FLOW")

    print("""
┌─ PROBLEM MESSAGE (2:00 PM) ─────────────────────────────────────┐
│                                                                  │
│  📝 Contains Duplicate                                           │
│  Pattern: Arrays & Hashing                                      │
│  Difficulty: Easy                                               │
│  🔗 https://leetcode.com/problems/contains-duplicate/            │
│                                                                  │
│  BUTTONS:                                                        │
│  [✅ Easy] [⏸️ Medium] [❌ Hard]                                   │
│  [💡 Hint] [📋 Solution] [⏭️ Skip]      ← SEE NEW BUTTON         │
│  [🏆 Done — I've mastered this]                                  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
                              ↓
                    User taps 📋 Solution
                              ↓
┌─ RESPONSE (via poll_mode) ──────────────────────────────────────┐
│                                                                  │
│  📋 Solution — Contains Duplicate                               │
│                                                                  │
│  ## APPROACH                                                     │
│  Use a hash set...                                              │
│                                                                  │
│  ## KEY INSIGHT                                                  │
│  Hash Set allows O(1) lookup...                                 │
│                                                                  │
│  ## JAVA CODE                                                    │
│  class Solution {                                               │
│      public boolean containsDuplicate(int[] nums) {             │
│          Set<Integer> seen = new HashSet<>();                   │
│          for (int num : nums) {                                 │
│              if (seen.contains(num)) return true;               │
│              seen.add(num);                                     │
│          }                                                       │
│          return false;                                          │
│      }                                                           │
│  }                                                               │
│                                                                  │
│  ## TIME & SPACE COMPLEXITY                                     │
│  - Time: O(n)  (single pass, O(1) lookup per element)           │
│  - Space: O(n) (worst case: all unique numbers)                 │
│                                                                  │
│  ## INTERVIEW EXPLANATION                                       │
│  1. "I'll use a hash set to track seen values"                 │
│  2. "This gives O(1) lookup which is critical"                 │
│  3. "Trade space for time — store numbers for linear time"     │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
""")

    print_section("5️⃣  IMPLEMENTATION DETAILS")

    print("""
How it works:

1. NEW BUTTON ADDED to create_difficulty_buttons():
   - Layout: [Hint] [📋 Solution] [Skip] (middle row)
   - Callback: "solution:INDEX"
   - Max bytes: "solution:174" = 13 bytes (well under 64-byte limit)

2. Handle in handle_button_callback():
   - Checks if action == "solution"
   - Returns: (title, None, "solution", problem)
   - Note: Stale button guard allows solution on mastered problems

3. Process in poll_mode():
   - Receives solution action
   - Calls generate_solution_preview(problem)
   - Returns Claude-generated solution in Java
   - Sends formatted message to Telegram

4. Claude prompt includes:
   - APPROACH: Core idea explanation
   - KEY INSIGHT: Interview-focused trick
   - JAVA CODE: Optimized, readable solution
   - COMPLEXITY: Time & Space both
   - INTERVIEW EXPLANATION: What to say in interviews
""")

    print_section("6️⃣  EXAMPLE: DIFFERENT PROBLEMS")

    examples = [
        {
            "title": "Two Sum",
            "approach": "Hash map stores complement values",
            "insight": "No need for nested loop — one pass!",
        },
        {
            "title": "Valid Parentheses",
            "approach": "Stack tracks opening brackets",
            "insight": "LIFO structure matches bracket nesting",
        },
        {
            "title": "Linked List Cycle",
            "approach": "Fast & slow pointers detect cycle",
            "insight": "They'll meet if cycle exists",
        },
    ]

    for ex in examples:
        print(f"\n{ex['title']}:")
        print(f"  APPROACH: {ex['approach']}")
        print(f"  INSIGHT:  {ex['insight']}")

    print_section("✅ SOLUTION BUTTON READY")

    print("""
The 📋 Solution button is now live and provides:

✓ Interview-ready Java code (not pseudo-code)
✓ Complexity analysis for both Time and Space
✓ Explanation of what to say in real interviews
✓ Mobile-friendly formatting for easy phone reading
✓ Generated by Claude API — always current

This is your personal DSA tutor in a button! 🚀

Next steps:
1. Deploy to Task Scheduler
2. Tap 📋 Solution on any problem
3. Study the approach and Java code
4. Explain to yourself using the interview explanation
5. Then solve it yourself to practice
""")

if __name__ == "__main__":
    demo_solution()
