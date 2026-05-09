# 📱 DSA SRS Bot - User Guide

## How to Use the Bot

The bot sends you 4 daily messages with study reminders and responds to your input in real-time.

---

## 🌅 Morning Session (7:00 AM)

**What you get:**
- Today's pattern explanation
- Main problem to solve
- 2-3 related problems in the same pattern
- Quick warm-up tip

**Buttons:**
- 📚 **Learn Pattern** - Deep dive into pattern theory
- 📖 **More Examples** - See 3 similar problems
- 💪 **I'm Ready** - Signal that you're ready to start

**Or type:**
```
"tell me more about this pattern"
"show me similar problems"
"i'm ready to start"
```

---

## ☀️ Afternoon Session (3:00 PM)

**What you get:**
- SRS review reminder (problems due today)
- Today's main problem with step-by-step guide
- Buttons for solving

**Buttons:**
- 💡 **Hint** - Get a Socratic hint (no spoilers)
- 📋 **Solution** - Full interview-ready solution
- ❓ **Stuck?** - Claude analyzes the problem and helps
- ✅ **I Solved It** - Mark as solved, then rate difficulty
- ⏸️ **Too Easy** - Increase difficulty for next problem
- ❌ **Too Hard** - Decrease difficulty for next problem

**Or type any of these:**
```
"I'm stuck"          → Get adaptive guidance
"show solution"      → Full solution
"too hard"           → Next problem is easier
"too easy"           → Next problem is harder
"I solved it"        → Rate the difficulty
```

---

## 📖 Evening Session (7:00 PM)

**What you get:**
- Summary of today's progress
- Problems due for SRS review
- Streak counter

**Buttons:**
- 📊 **My Stats** - View learning progress & streak
- 📈 **Weak Areas** - See patterns you struggle with
- 📝 **Create Plan** - Get recommended study schedule

**Or type:**
```
"show my stats"      → View progress
"weak areas"         → See struggling patterns
"create a plan"      → Get study schedule
```

---

## 🌙 Night Session (10:00 PM)

**What you get:**
- Pattern summary from today
- Key insight and approach
- Similar problems review
- Tomorrow's problem preview

No buttons (read-only summary). Helps you consolidate learning before sleep.

---

## 💬 Free-Form Chat (Anytime)

You can type **anything** and the bot will understand:

### Request Help
```
"I'm stuck on step 2"
"Help me understand two pointers"
"How do I approach this?"
```
→ **Response:** Socratic hint with guiding questions

### Request Solution
```
"show solution"
"reveal answer"
"I give up, show me"
```
→ **Response:** Full interview-ready solution

### Adjust Difficulty
```
"This was too easy"
"Too hard, make it easier"
"Harder problem please"
```
→ **Response:** Tracks feedback, adjusts next problem

### View Progress
```
"my stats"
"how many problems solved"
"show progress"
```
→ **Response:** Statistics card with all metrics

### Find Weak Areas
```
"what should I focus on"
"weak areas"
"struggling with"
```
→ **Response:** Analysis of patterns you struggle with

### Get Study Plan
```
"what's the plan"
"how should I study"
"suggest a schedule"
```
→ **Response:** Recommended daily study routine

### Ask Questions
```
"what is sliding window?"
"explain two pointers"
"how do I debug this?"
```
→ **Response:** Claude answers contextually

---

## 📊 Understanding Your Stats

When you tap **"📊 My Stats"** or type "show my stats":

```
📊 Your Learning Stats

🎯 Progress:
  • Total problems: 175       (how many in the system)
  • New: 172 | Active: 3      (statuses)
  • Mastered: 0               (completed patterns)
  • Total reviews: 3          (how many times you've reviewed)
  • Avg. ease factor: 2.50    (how easy problems feel to you)

🔥 Streak: 1 days             (consecutive study days)
✅ Problems solved: 3         (total completed)
⏱️ Last updated: 2026-05-09   (when you last studied)
```

---

## 📈 Weak Areas Analysis

When you tap **"📈 Weak Areas"** or type "weak areas":

The bot analyzes:
- Problems you've reviewed **more than 3 times** (suggests you find them hard)
- Patterns with **low ease factor** (< 1.5 means you struggle)
- Gives specific recommendations

Example:
```
📈 Areas to Focus On

Based on your performance:
  • Arrays & Hashing: 2 problem(s) to revisit
  • Two Pointers: 1 problem(s) to revisit

💡 Tip: Revisit these patterns by solving 
similar problems. Each attempt strengthens 
your understanding!
```

---

## ✅ Rating Your Difficulty

After you solve a problem, tap one of:
- ✅ **Easy** - Problem was straightforward, you solved it fast
- ⏸️ **Medium** - Moderate difficulty, took some thinking
- ❌ **Hard** - Challenging, took a long time or needed help

**The bot uses your rating to:**
1. **Space out reviews** - Easy problems return later, hard ones sooner
2. **Adjust difficulty** - Next problem matches your level
3. **Track progress** - Shows improvement over time

---

## 🏆 Mastering Problems

Once you've solved a problem multiple times and feel confident:
- Tap **"🏆 Mastered"** button (on default button set)
- Or type: **"I've mastered this"**

The problem is **archived** and won't appear in reviews anymore.

---

## 🔄 Daily Routine

**7:00 AM** 🌅
- Receive morning pattern explanation
- Tap "💪 I'm Ready"

**Mid-morning** ✏️
- 5-30 minutes: Learn the pattern theory
- Read the explanation and examples

**3:00 PM** ☀️
- Receive afternoon problem + guides
- 30 minutes: Solve the problem
- Rate difficulty when done

**7:00 PM** 📖
- Receive evening review reminder
- 20 minutes: Review any due problems
- Check your stats & weak areas

**10:00 PM** 🌙
- Receive night summary
- 5 minutes: Read consolidation material
- Sleep well, you earned it!

---

## 💡 Pro Tips

### 1. **Don't Use Solution Right Away**
Tap "❓ Stuck?" first for a hint. Try again. Only request solution after 10+ minutes.

### 2. **Be Honest About Difficulty**
Your rating trains the system. Don't say "easy" if you struggled.

### 3. **Revisit Weak Areas**
When you see weak pattern analysis, dedicate extra time to those problems.

### 4. **Track Your Streak**
The streak counter is powerful motivation. Keep the chain unbroken!

### 5. **Ask Questions Freely**
The bot understands natural language. Type like you're chatting with a mentor.

---

## ❓ FAQ

**Q: What if I miss a session?**
A: No penalty. Just pick up next time. The system adapts.

**Q: Can I change problem difficulty?**
A: Yes! Tap "Too Easy" or "Too Hard" and the next problem adjusts.

**Q: How often should I review problems?**
A: The bot uses spaced repetition. Easy problems: every 2 weeks. Hard: every 1-2 days.

**Q: What does "Ease Factor" mean?**
A: 2.5 = you find it very easy. 1.3 = you find it hard. Higher is better.

**Q: Can I skip the morning session?**
A: Yes, you can work offline and catch up in afternoon session.

**Q: How do I get better at weak areas?**
A: Solve 2-3 similar problems from that pattern until you master it.

---

## 🎯 Study Philosophy

**This bot is designed for:**
- ✅ Consistent daily practice
- ✅ Spaced repetition (reviews at optimal intervals)
- ✅ Adaptive difficulty (challenging but not overwhelming)
- ✅ Active learning (solve, rate, reflect)
- ✅ Mentorship (hints guide your thinking)

**Not for:**
- ❌ Cramming (consistency beats intensity)
- ❌ Speed (quality understanding over quantity)
- ❌ Passively reading solutions

---

## 🚀 Getting Started

1. **Receive morning message** with pattern explanation
2. **Tap a button or type a message** to interact
3. **Solve the problem** (30 minutes)
4. **Rate your difficulty** (✅ / ⏸️ / ❌)
5. **Check evening stats** (see progress)
6. **Review weak areas** (focus next time)
7. **Repeat daily** for mastery 💪

---

**Remember:** Consistency beats perfection. Study every day, and you'll master DSA faster than you think! 🎓

