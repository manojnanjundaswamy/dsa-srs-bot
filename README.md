# DSA SRS Bot: Personal AI Coach for Interview Prep

<div align="center">

![Status](https://img.shields.io/badge/status-production%20ready-brightgreen)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

**Your AI-powered spaced repetition system for mastering data structures & algorithms in Java**

[Features](#-features) • [Quick Start](#-quick-start) • [Daily Workflow](#-daily-workflow) • [Documentation](#-documentation)

</div>

---

## 🎯 What is DSA SRS Bot?

A personal **Telegram-based AI coach** that delivers daily coding problems with:
- **Spaced repetition scheduling** (SM-2 algorithm) to reinforce learning
- **Interactive Telegram buttons** for instant feedback and hints
- **AI-generated Java solutions** with interview explanations
- **Complexity analysis** (time & space) for every problem
- **175 curated LeetCode problems** organized by pattern

**No browser, no app**. Everything happens in Telegram on your phone. Perfect for interview prep.

---

## ✨ Features

### 🤖 AI-Powered Content
- **Java Code Solutions** — Real, runnable code (not pseudo-code)
- **Claude-Generated Hints** — Targeted hints when you're stuck
- **Interview Explanations** — Exactly what to say in interviews
- **Pattern Recognition** — Learn by pattern, not random problems

### 📱 Interactive Telegram Interface
- **7 Action Buttons per Problem:**
  - ✅ **Easy** — Solved quickly → review in 3 days
  - ⏸️ **Medium** — Took thinking → review in 1 day
  - ❌ **Hard** — Struggled → review in 1 day + lower confidence
  - 💡 **Hint** — Get a Claude-generated hint
  - 📋 **Solution** — Full Java code + complexity + interview explanation
  - ⏭️ **Skip** — Defer to tomorrow
  - 🏆 **Done** — Archive when mastered (won't reappear)

### 📊 Smart Scheduling
- **SM-2 Spaced Repetition** — Optimal review intervals automatically calculated
- **Status Lifecycle** — Problems progress: new → active → mastered
- **Pattern Completion** — Celebrates when you finish a pattern
- **Due Problems First** — Always shows what you should review first

### ⏰ 4 Daily Modes
- **7:00 AM** — Morning overview of today's pattern & main problem
- **2:00 PM** — Problem with 7 interactive buttons
- **6:00 PM** — Evening review reminders (due problems)
- **9:00 PM** — Night summary + tomorrow's preview
- **Every 5 min** — Poll mode processes your button taps

### 📚 Well-Organized Problems
175 LeetCode problems sorted by:
- **15+ Patterns:** Arrays, Linked Lists, Trees, Graphs, DP, etc.
- **Difficulty:** Easy → Medium → Hard progression
- **Interview Focus:** Companies ask these patterns repeatedly

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Telegram account
- [Anthropic API key](https://console.anthropic.com)
- Optional: [Telegram bot token](https://t.me/BotFather)

### 1. Clone & Install

```bash
git clone https://github.com/yourusername/dsa-srs-bot.git
cd dsa-srs-bot
pip install -r requirements.txt
```

### 2. Configure

```bash
# Copy the example config
cp .env.example .env

# Edit .env with your keys:
# ANTHROPIC_API_KEY=your_claude_api_key
# TELEGRAM_BOT_TOKEN=your_telegram_bot_token
# CHAT_ID=your_telegram_chat_id
```

**Get your chat ID:**
- Send any message to your bot
- Run: `curl https://api.telegram.org/botYOUR_TOKEN/getUpdates`
- Look for `"chat":{"id":YOUR_CHAT_ID}`

### 3. Verify Setup

```bash
python quick_verify.py
```

Expected output: ✅ All checks pass (except Task Scheduler tasks, not yet created)

### 4. Test a Mode

```bash
# Send afternoon problem to Telegram
python reminder_bot.py --mode=afternoon

# Check Telegram for the message with 7 buttons
# Tap 📋 Solution to see Java code
```

### 5. Schedule Automatic Reminders (Optional)

Follow **[TASK_SCHEDULER_SETUP.md](TASK_SCHEDULER_SETUP.md)** to create 5 Windows Task Scheduler tasks:
- Morning (7 AM)
- Afternoon (2 PM)
- Evening (6 PM)
- Night (9 PM)
- Poll (every 5 minutes)

Once enabled, the bot sends problems automatically.

---

## 📅 Daily Workflow

### Morning (7:00 AM)
```
🌅 Good Morning!
📚 Today's Pattern: Arrays & Hashing
🎯 Main Problem: Contains Duplicate (LeetCode #217)
Difficulty: Easy
🔗 https://leetcode.com/problems/contains-duplicate/
```

### Afternoon (2:00 PM)
```
📝 Contains Duplicate
Pattern: Arrays & Hashing
Difficulty: Easy
URL: https://leetcode.com/problems/contains-duplicate/

Key Insight: Hash Set allows O(1) lookup
Step-by-Step Approach:
  1. Create empty hash set
  2. Iterate through array
  3. If number seen, return true
  4. Otherwise, add to set

Java Code Skeleton:
class Solution {
    public boolean containsDuplicate(int[] nums) {
        Set<Integer> seen = new HashSet<>();
        // Complete the solution...
    }
}

Ready to solve it? Tap a difficulty button below after you're done!

[✅ Easy] [⏸️ Medium] [❌ Hard]
[💡 Hint] [📋 Solution] [⏭️ Skip]
[🏆 Done — I've mastered this]
```

### When You Tap 📋 Solution
```
📋 Solution — Contains Duplicate

## APPROACH
Use a hash set to track seen numbers. As you iterate through the array,
check if each number exists in the set. If it does, we found a duplicate.

## KEY INSIGHT
Hash Set allows O(1) lookup — this is the interviewer's expected trick!

## JAVA CODE
class Solution {
    public boolean containsDuplicate(int[] nums) {
        Set<Integer> seen = new HashSet<>();
        for (int num : nums) {
            if (seen.contains(num)) return true;
            seen.add(num);
        }
        return false;
    }
}

## TIME & SPACE COMPLEXITY
- Time: O(n) — single pass, O(1) lookup per element
- Space: O(n) — worst case all unique numbers

## INTERVIEW EXPLANATION
1. Say: "I'll use a hash set to track seen values"
2. Mention: "This gives O(1) lookup which is critical"
3. Explain: "Trade space for time — store numbers for linear time"
```

### Evening (6:00 PM)
Problems due for review today + status update

### Night (9:00 PM)
Summary of pattern + tomorrow's problem preview

---

## 🏗️ Project Structure

```
dsa-srs-bot/
├── reminder_bot.py                # Main bot (1600+ lines)
├── dsa_tracker.json               # 175 problems database
├── requirements.txt               # Python dependencies
├── .env.example                   # Config template
├── .gitignore                     # Sensitive files excluded
│
├── README.md                      # This file
├── README_DEPLOYMENT.md           # Full deployment guide
├── TASK_SCHEDULER_SETUP.md        # Windows Task Scheduler setup
├── JAVA_SOLUTION_BUTTON_CHANGES.md # Feature changelog
│
├── test_*.py                      # Demo & verification scripts
├── setup_tasks.ps1                # Task creation helper
├── quick_verify.py                # Setup verification
│
└── logs/                          # Daily execution logs
    └── dsa_bot_2026-05-09.log
```

---

## 🔧 How It Works

### Architecture

```
┌─────────────────────────────────────────────┐
│         Windows Task Scheduler               │
│  (Triggers at 7 AM, 2 PM, 6 PM, 9 PM, etc) │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │   reminder_bot.py    │
        │                      │
        │ • Load problems      │
        │ • Generate message   │
        │ • Get Claude hints   │
        │ • Track SRS status   │
        └──────────────────────┘
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
   ┌─────────────────┐  ┌────────────────┐
   │  Claude API     │  │  Telegram API  │
   │                 │  │                │
   │ • Hints         │  │ • Send message │
   │ • Solutions     │  │ • Receive taps │
   │ • Explanations  │  │ • Answer poll  │
   └─────────────────┘  └────────────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │   dsa_tracker.json   │
        │                      │
        │ Problem statuses:    │
        │ • new (to learn)     │
        │ • active (in SRS)    │
        │ • mastered (done)    │
        │                      │
        │ Next due date        │
        │ Review intervals     │
        └──────────────────────┘
```

### SM-2 Spaced Repetition Algorithm

When you tap a difficulty button:

```
✅ Easy (solved in <15 min)
  → Next review in 3 days
  → Confidence boost

⏸️ Medium (took some thinking)
  → Next review in 1 day
  → Maintain confidence

❌ Hard (struggled / used hints)
  → Next review in 1 day
  → Lower confidence (easier problems next)
```

The algorithm ensures you review problems right before you forget them.

---

## 📖 Documentation

| Document | Purpose |
|----------|---------|
| **[README_DEPLOYMENT.md](README_DEPLOYMENT.md)** | Full setup, features, troubleshooting |
| **[TASK_SCHEDULER_SETUP.md](TASK_SCHEDULER_SETUP.md)** | Windows Task Scheduler step-by-step |
| **[JAVA_SOLUTION_BUTTON_CHANGES.md](JAVA_SOLUTION_BUTTON_CHANGES.md)** | Feature implementation details |

### Quick Commands

```bash
# Run a specific mode
python reminder_bot.py --mode=afternoon
python reminder_bot.py --mode=morning
python reminder_bot.py --mode=evening
python reminder_bot.py --mode=night
python reminder_bot.py --mode=poll

# Verify your setup
python quick_verify.py

# View today's logs
Get-Content "logs\dsa_bot_$(Get-Date -Format 'yyyy-MM-dd').log" -Tail 50
```

---

## 🎓 Use Cases

### 1. **Interview Prep (Best Use)**
- 3-month sprint before interviews
- 1 problem per day = 90 problems mastered
- Interview explanations for every solution
- Complexity analysis practiced daily

### 2. **LeetCode Grinding**
- Spaced repetition prevents forgetting
- Patterns group similar problems
- Hints guide discovery learning

### 3. **Pattern Mastery**
- Learn one pattern deeply
- Auto-completion detection
- Progress visualization

### 4. **Daily Habit**
- 5-10 min morning + afternoon + evening
- Telegram notifications (no email fatigue)
- Mobile-friendly on phone/tablet

---

## 💡 Examples

### Problem: Two Sum
```
Pattern: Hash Map
Difficulty: Easy

When you tap 📋 Solution:
- APPROACH: Hash map stores complement
- KEY INSIGHT: O(n) vs nested loop O(n²)
- JAVA CODE: Real implementation
- COMPLEXITY: O(n) time, O(n) space
- INTERVIEW: "I'll store complements in a hash map for O(1) lookup"
```

### Problem: Binary Tree Level Order
```
Pattern: BFS/Queue
Difficulty: Medium

When you tap 💡 Hint:
- "Try using a queue data structure"
- "Process level by level"
- "Store node children for next iteration"
```

---

## 📊 Problem Database

**175 LeetCode problems** organized by:

| Pattern | Count |
|---------|-------|
| Arrays & Hashing | 12 |
| Two Pointers | 8 |
| Sliding Window | 7 |
| Stack & Queue | 10 |
| Linked Lists | 12 |
| Trees | 25 |
| Graphs | 20 |
| Heaps | 8 |
| Binary Search | 6 |
| DP | 30 |
| Backtracking | 12 |
| Greedy | 8 |
| Trie | 5 |
| Advanced | 12 |

**All with:**
- ✅ Java solutions (not pseudo-code)
- ✅ Time & space complexity
- ✅ Interview explanations
- ✅ Pattern grouping

---

## ⚙️ Configuration

### `.env` File

```bash
# Anthropic Claude API
ANTHROPIC_API_KEY=sk-ant-xxx

# Telegram Bot
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
CHAT_ID=123456789
```

**Get these:**
1. **Anthropic API:** https://console.anthropic.com
2. **Telegram Token:** Chat with [@BotFather](https://t.me/BotFather)
3. **Telegram Chat ID:** Send any message to your bot, then:
   ```bash
   curl "https://api.telegram.org/botYOUR_TOKEN/getUpdates"
   ```

---

## 🐛 Troubleshooting

### No message in Telegram
1. Check `.env` has correct tokens
2. Check internet connection
3. View logs: `logs/dsa_bot_2026-05-09.log`

### Solution button doesn't respond
1. Check Claude API quota
2. Verify `ANTHROPIC_API_KEY` in `.env`
3. Check logs for "Claude API" errors

### Task Scheduler tasks don't run
1. Verify Python path is correct in task
2. Right-click task → **Enable**
3. Right-click task → **Run** (manual test)
4. Check Event Viewer for errors

See **[README_DEPLOYMENT.md](README_DEPLOYMENT.md)** for more troubleshooting.

---

## 📈 Verification

Run the verification script to check your setup:

```bash
python quick_verify.py
```

**Should show:**
- ✅ Python 3.10+
- ✅ Dependencies installed (anthropic, requests, python-dotenv)
- ✅ Config files present (.env, .env.example)
- ✅ Problem database (dsa_tracker.json with 175 problems)
- ✅ New features (Solution button, hint generation, etc.)
- ⏳ Task Scheduler tasks (not created yet, optional)

---

## 🤝 Contributing

This is a personal project, but improvements are welcome!

1. Fork the repo
2. Create a branch: `git checkout -b feature/your-feature`
3. Make changes
4. Commit: `git commit -m "Add your feature"`
5. Push: `git push origin feature/your-feature`
6. Open a pull request

### Ideas for Contribution
- Additional problem patterns
- More interview explanations
- Statistics dashboard
- Mobile app wrapper
- Database export formats

---

## 📜 License

MIT License — See LICENSE file for details

---

## 🎉 Getting Started

1. **Clone:** `git clone https://github.com/yourusername/dsa-srs-bot.git`
2. **Install:** `pip install -r requirements.txt`
3. **Configure:** Copy `.env.example` → `.env` and add your keys
4. **Verify:** `python quick_verify.py`
5. **Test:** `python reminder_bot.py --mode=afternoon`
6. **Schedule:** Follow `TASK_SCHEDULER_SETUP.md` (optional)

**Start solving problems in Telegram within 5 minutes!**

---

## 📞 Support

- **Questions?** Check the documentation files
- **Issues?** Run `quick_verify.py` and check logs
- **Feedback?** Open an issue on GitHub

---

<div align="center">

**Made with ❤️ for interview prep**

*Master DSA patterns. Ace your interviews.*

</div>
