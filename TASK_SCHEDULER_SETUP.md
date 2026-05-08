# Task Scheduler Setup & Verification Guide

## Overview
The DSA SRS bot runs on Windows Task Scheduler to send reminders at specific times each day:
- **Morning (7:00 AM)** — Daily problem overview + pattern explanation
- **Afternoon (2:00 PM)** — Problem with buttons to rate difficulty
- **Evening (6:00 PM)** — SRS review reminders
- **Night (9:00 PM)** — Summary + tomorrow's preview
- **Poll (Every 5 min)** — Check for button taps and process ratings

---

## Step 1: Verify Python & Dependencies

### 1.1 Check Python Installation
```powershell
python --version
# Should output: Python 3.10+ or later

# Verify it's in PATH
where python
# Should show: C:\Users\manoj\AppData\Local\Programs\Python\Python3XX\python.exe
```

### 1.2 Verify Required Packages
```powershell
pip list | findstr "anthropic requests python-dotenv"
# Should show:
# anthropic           0.xx.x
# requests            2.xx.x
# python-dotenv       1.x.x
```

If any are missing:
```powershell
pip install anthropic requests python-dotenv
```

### 1.3 Verify .env File Exists
```powershell
ls "d:\Claude_Playground\Job and Interview Helper\.env"
# File should exist with:
# ANTHROPIC_API_KEY=sk-ant-...
# TELEGRAM_BOT_TOKEN=8758562298:AAG...
# CHAT_ID=5466701469
```

---

## Step 2: Verify Bot Configuration

### 2.1 Test Bot Manually (No Task Scheduler)
```powershell
cd "d:\Claude_Playground\Job and Interview Helper"

# Test morning mode
python reminder_bot.py --mode morning
# Should output: ✅ Morning prep sent...

# Test afternoon mode
python reminder_bot.py --mode afternoon
# Should show problem with buttons

# Test evening mode
python reminder_bot.py --mode evening
# Should output: ✅ Evening review reminder sent

# Test night mode
python reminder_bot.py --mode night
# Should output: ✅ Night summary sent

# Test poll mode
python reminder_bot.py --mode poll
# Should output: ✅ Poll complete: 0 update(s) processed
```

✅ **Success:** All modes run without errors

### 2.2 Verify Telegram Integration
After running any mode above, check Telegram for messages with:
- Morning: Pattern explanation + problem overview
- Afternoon: Problem with all 7 buttons visible (Easy, Medium, Hard, Hint, Solution, Skip, Done)
- Evening: Review list + main problem status
- Night: Summary + tomorrow preview

✅ **Success:** Messages arrive with proper formatting and buttons visible

---

## Step 3: Set Up Task Scheduler

### 3.1 Open Task Scheduler
```powershell
taskschd.msc
# Or: Ctrl+R → taskschd.msc → Enter
```

### 3.2 Create Morning Task (7:00 AM)

1. **Right-click** "Task Scheduler Library" → **"Create Basic Task"**
2. **Name:** `DSA Bot - Morning (7 AM)`
3. **Description:** `Send daily DSA problem at 7 AM`
4. **Trigger:**
   - Select: Daily
   - Start date: [Today's date]
   - Recur every: 1 day
   - Time: **07:00:00**
5. **Action:**
   - Program: `C:\Users\manoj\AppData\Local\Programs\Python\Python3XX\python.exe`
   - Arguments: `"d:\Claude_Playground\Job and Interview Helper\reminder_bot.py" --mode morning`
   - Start in: `d:\Claude_Playground\Job and Interview Helper`
6. **Finish**

### 3.3 Create Afternoon Task (2:00 PM)
- Name: `DSA Bot - Afternoon (2 PM)`
- Trigger: Daily at **14:00:00**
- Arguments: `"d:\Claude_Playground\Job and Interview Helper\reminder_bot.py" --mode afternoon`

### 3.4 Create Evening Task (6:00 PM)
- Name: `DSA Bot - Evening (6 PM)`
- Trigger: Daily at **18:00:00**
- Arguments: `"d:\Claude_Playground\Job and Interview Helper\reminder_bot.py" --mode evening`

### 3.5 Create Night Task (9:00 PM)
- Name: `DSA Bot - Night (9 PM)`
- Trigger: Daily at **21:00:00**
- Arguments: `"d:\Claude_Playground\Job and Interview Helper\reminder_bot.py" --mode night`

### 3.6 Create Poll Task (Every 5 Minutes)
1. **Name:** `DSA Bot - Poll (Every 5 min)`
2. **Description:** `Check for button taps every 5 minutes`
3. **Trigger:**
   - Select: Daily
   - Time: **00:00:00**
   - **Repeat task every:** `5 minutes`
   - **Duration:** `Indefinitely`
4. **Action:**
   - Arguments: `"d:\Claude_Playground\Job and Interview Helper\reminder_bot.py" --mode poll`

---

## Step 4: Verify Task Scheduler Configuration

### 4.1 List All Scheduled Tasks
```powershell
Get-ScheduledTask | Where-Object {$_.TaskName -like "*DSA*"} | Format-Table TaskName, State

# Should output 5 tasks, all with State = "Ready"
```

### 4.2 Manually Run a Task to Test
```powershell
# Run morning task now (don't wait until 7 AM)
Start-ScheduledTask -TaskName "DSA Bot - Morning (7 AM)"

# Check Telegram within 10 seconds for the message
# Verify message appears and buttons render correctly
```

✅ **Success:** Message appears in Telegram with buttons visible

### 4.3 Check Task History
```powershell
Get-ScheduledTask "DSA Bot - Morning (7 AM)" | Get-ScheduledTaskInfo | 
  Select LastRunTime, LastTaskResult

# LastTaskResult should be 0 (success)
```

---

## Step 5: Troubleshoot

### If tasks don't run:
```powershell
# 1. Enable the task
Enable-ScheduledTask -TaskName "DSA Bot - Morning (7 AM)"

# 2. Verify Python path
python -c "import sys; print(sys.executable)"
# Use this exact path in Task Scheduler

# 3. Check .env file
Test-Path "d:\Claude_Playground\Job and Interview Helper\.env"
# Should return: True
```

### If messages don't appear in Telegram:
```powershell
# 1. Test manually
python reminder_bot.py --mode morning

# 2. Check log file
Get-Content "d:\Claude_Playground\Job and Interview Helper\logs\dsa_bot_$(Get-Date -Format 'yyyy-MM-dd').log" -Tail 20
```

---

## New Feature: Solution Button

### 📋 Solution Button (NEW!)
The Problem message now includes a **Solution** button that provides:

**Button Layout:**
```
[✅ Easy]  [⏸️ Medium]  [❌ Hard]
[💡 Hint]  [📋 Solution]  [⏭️ Skip]
[🏆 Done — I've mastered this]
```

**When tapped, returns:**
```
📋 Solution — Problem Title

## APPROACH
[2-3 sentences explaining the core idea]

## KEY INSIGHT  
[Main trick/observation for interviews]

## JAVA CODE
```java
class Solution {
    public ReturnType methodName(Parameters) {
        // Best solution in Java (max 15 lines)
        // Optimized and readable
    }
}
```

## TIME & SPACE COMPLEXITY
- Time: O(...)
- Space: O(...)

## INTERVIEW EXPLANATION
When explaining in an interview:
1. [First key point to mention]
2. [Second key point to mention]
3. [Third key point to mention]
```

**Advantages:**
- ✅ Java code (not Python) — matches your DSA work
- ✅ Mobile-friendly formatting — easy to read on phone/tablet
- ✅ Interview-focused — explains what to say in interviews
- ✅ Complexity analysis — both time and space
- ✅ Read-only action — doesn't change problem state
- ✅ Works on mastered problems too

---

## Daily Workflow

**7:00 AM** → Morning message with problem overview  
**Solve the problem** → Write Java code  
**2:00 PM** → Afternoon message with problem + 7 buttons  
   - 📋 Tap Solution to see formatted Java solution & complexity
   - ✅/⏸️/❌ Tap difficulty rating after solving  
   - 💡 Tap Hint if stuck  
   - ⏭️ Tap Skip to defer  
**6:00 PM** → Evening review reminders  
**9:00 PM** → Night summary + tomorrow preview  
**Every 5 min** → Poll checks for button taps  

---

## Verification Checklist

- [ ] Python 3.10+ installed
- [ ] anthropic, requests, python-dotenv packages installed
- [ ] .env file exists with API keys
- [ ] Manual test: `python reminder_bot.py --mode morning` works
- [ ] Telegram message appears with buttons
- [ ] 5 Task Scheduler tasks created (Morning, Afternoon, Evening, Night, Poll)
- [ ] All tasks show State = "Ready"
- [ ] Manual trigger test: Task runs immediately when triggered
- [ ] Telegram confirms message arrives within 10 seconds
- [ ] Solution button visible on problem messages (NEW!)
- [ ] Solution button works and returns formatted Java code (NEW!)

---

**Status:** ✅ Production Ready  
**Last Updated:** 2026-05-09  
**Java Support:** ✅ Enabled  
**Solution Button:** ✅ Active
