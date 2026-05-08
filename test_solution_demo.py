#!/usr/bin/env python3
"""
SOLUTION BUTTON DEMO
Shows exactly what you'll get when you tap the 📋 Solution button in Telegram
"""

import json
import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

SCRIPT_DIR = Path(__file__).parent
TRACKER_FILE = SCRIPT_DIR / "dsa_tracker.json"

# Load tracker
with open(TRACKER_FILE) as f:
    tracker = json.load(f)

# Get the first new problem (same as afternoon mode)
problem = next(p for p in tracker['problems'] if p['status'] == 'new')

print("\n" + "█"*80)
print("█" + "  📋 SOLUTION BUTTON RESPONSE PREVIEW".center(78) + "█")
print("█"*80)

print(f"\n✅ Problem: {problem['title']}")
print(f"📌 Pattern: {problem['pattern']}")
print(f"🔗 LeetCode: {problem['leetcode_url']}\n")

# Show what to do
print("="*80)
print("  WHEN YOU TAP 📋 SOLUTION IN TELEGRAM:")
print("="*80)

demo_response = f"""
📋 Solution — {problem['title']}

## APPROACH
Use a fast and slow pointer technique. If a cycle exists in the array where values
serve as indices, the pointers will eventually meet at the cycle start.

## KEY INSIGHT
Floyd's Cycle Detection Algorithm — the slow pointer moves 1 step, fast moves 2 steps.
When fast catches slow, we've found the cycle!

## JAVA CODE
<pre><code>class Solution {{
    public int findDuplicate(int[] nums) {{
        int slow = nums[0], fast = nums[0];

        // Detect cycle
        do {{
            slow = nums[slow];
            fast = nums[nums[fast]];
        }} while (slow != fast);

        // Find entry point
        slow = nums[0];
        while (slow != fast) {{
            slow = nums[slow];
            fast = nums[fast];
        }}
        return slow;
    }}
}}</code></pre>

## TIME & SPACE COMPLEXITY
- Time: O(n) — single pass with two pointers
- Space: O(1) — no extra storage needed

## INTERVIEW EXPLANATION
1. Say: "I'll use Floyd's cycle detection with two pointers"
2. Mention: "O(n) time without extra space makes this optimal"
3. Explain: "The fast pointer catches the slow one if a cycle exists"
"""

print(demo_response)

print("="*80)
print("  YOUR RESPONSE OPTIONS AFTER GETTING THE SOLUTION:")
print("="*80)

print("""
After reading the solution above, you have 4 choices:

1. 📝 IMPLEMENT & SOLVE
   • Close Telegram, write your own Java code
   • Implement the approach in your IDE
   • Test with LeetCode

2. ✅ TAP 'EASY' BUTTON
   • You solved it in < 15 minutes
   • Next review in 3 days

3. ⏸️ TAP 'MEDIUM' BUTTON
   • You solved it but took a while
   • Next review in 1 day

4. ❌ TAP 'HARD' BUTTON
   • You struggled or needed hints
   • Next review in 1 day + lower confidence

5. 💡 TAP 'HINT' BUTTON (instead of Solution)
   • Get a shorter hint if you want to try solving first
   • Then come back for full solution if stuck

6. ⏭️ TAP 'SKIP'
   • Try another problem today
   • This one reappears tomorrow

7. 🏆 TAP 'DONE'
   • I've mastered this pattern
   • Never appears in review queue again
""")

print("\n" + "="*80)
print("  KEY THINGS TO NOTICE:")
print("="*80)

print("""
✅ CODE IS IN JAVA (not Python)
   • Real Java syntax you can copy-paste into LeetCode
   • Not pseudo-code — fully working solution

✅ COMPLEXITY EXPLAINED
   • Time: O(n) means linear time
   • Space: O(1) means no extra memory needed
   • This is what interviewers care about

✅ INTERVIEW EXPLANATION
   • Three specific points to mention
   • Exactly what to say when asked in interviews
   • Shows you understand the "why" not just the code

✅ MOBILE FORMATTED
   • Long lines are wrapped
   • Code is indented clearly
   • Easy to read on phone/tablet

✅ PATTERN AWARE
   • Ties back to the pattern: "Fast and Slow Pointer"
   • Helps you remember technique for similar problems
   • You'll see other fast/slow pointer problems later
""")

print("\n" + "="*80)
print("  NEXT STEPS:")
print("="*80)

print(f"""
1. 📱 Go to Telegram
2. 🔍 Find problem message: "{problem['title']}"
3. 📋 Tap the [📋 Solution] button
4. ⏳ Wait 2-3 seconds for Claude to generate
5. ✨ See the full Java solution with explanation
6. 💻 Implement it yourself
7. ✅ Tap ✅/⏸️/❌ to rate difficulty
8. 🔄 Problem automatically scheduled for review

The full flow ends in Telegram — no coding required after you read the solution!
""")

print("█"*80 + "\n")
