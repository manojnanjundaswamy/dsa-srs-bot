# Quick Task Scheduler Verification Script
# Run this to verify your DSA bot setup is correct
# Usage: .\QUICK_VERIFY.ps1

Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║         DSA SRS BOT — TASK SCHEDULER VERIFICATION            ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

$checks_passed = 0
$checks_total = 0

function Check-Item {
    param($Name, $Command, $ExpectedPattern)
    $checks_total++

    Write-Host "⏳ Checking: $Name..." -ForegroundColor Yellow

    try {
        $result = Invoke-Expression $Command

        if ($result -match $ExpectedPattern) {
            Write-Host "✅ PASS: $Name" -ForegroundColor Green
            Write-Host "   Result: $($result -replace "`n", "`n   ")`n"
            $checks_passed++
            return $true
        } else {
            Write-Host "❌ FAIL: $Name" -ForegroundColor Red
            Write-Host "   Expected pattern: $ExpectedPattern" -ForegroundColor Red
            Write-Host "   Got: $result`n" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Write-Host "❌ ERROR: $Name" -ForegroundColor Red
        Write-Host "   Error: $_`n" -ForegroundColor Red
        return $false
    }
}

# ============ STEP 1: Python & Dependencies ============
Write-Host "┌─ STEP 1: Python & Dependencies ─────────────────────────────┐" -ForegroundColor Blue
Write-Host ""

Check-Item "Python installed" "python --version" "Python 3\."
Check-Item "anthropic package" "pip show anthropic" "Name: anthropic"
Check-Item "requests package" "pip show requests" "Name: requests"
Check-Item "python-dotenv package" "pip show python-dotenv" "Name: python-dotenv"

Write-Host ""

# ============ STEP 2: Files & Configuration ============
Write-Host "┌─ STEP 2: Files & Configuration ────────────────────────────┐" -ForegroundColor Blue
Write-Host ""

$botPath = "d:\Claude_Playground\Job and Interview Helper"

# Check bot file exists
if (Test-Path "$botPath\reminder_bot.py") {
    Write-Host "✅ PASS: reminder_bot.py exists" -ForegroundColor Green
    $checks_passed++
} else {
    Write-Host "❌ FAIL: reminder_bot.py not found" -ForegroundColor Red
}
$checks_total++

# Check .env file exists
if (Test-Path "$botPath\.env") {
    Write-Host "✅ PASS: .env file exists" -ForegroundColor Green
    $checks_passed++
} else {
    Write-Host "❌ FAIL: .env file not found" -ForegroundColor Red
}
$checks_total++

# Check .env has keys
if ((Get-Content "$botPath\.env") -match "ANTHROPIC_API_KEY" -and (Get-Content "$botPath\.env") -match "TELEGRAM_BOT_TOKEN") {
    Write-Host "✅ PASS: .env contains API keys" -ForegroundColor Green
    $checks_passed++
} else {
    Write-Host "❌ FAIL: .env missing API keys" -ForegroundColor Red
}
$checks_total++

# Check tracker file exists
if (Test-Path "$botPath\dsa_tracker.json") {
    Write-Host "✅ PASS: dsa_tracker.json exists" -ForegroundColor Green
    $checks_passed++
} else {
    Write-Host "❌ FAIL: dsa_tracker.json not found" -ForegroundColor Red
}
$checks_total++

Write-Host ""

# ============ STEP 3: Manual Test ============
Write-Host "┌─ STEP 3: Manual Test (Morning Mode) ───────────────────────┐" -ForegroundColor Blue
Write-Host ""
Write-Host "Running: python reminder_bot.py --mode morning" -ForegroundColor Yellow
Write-Host "This will send a test message to Telegram..." -ForegroundColor Gray
Write-Host ""

Set-Location $botPath
$morningTest = & python reminder_bot.py --mode morning 2>&1 | Select-String -Pattern "Morning prep sent|ERROR|Exception"

if ($morningTest -match "Morning prep sent") {
    Write-Host "✅ PASS: Morning mode executed successfully" -ForegroundColor Green
    $checks_passed++
} elseif ($morningTest -match "ERROR|Exception") {
    Write-Host "❌ FAIL: Morning mode encountered an error:" -ForegroundColor Red
    Write-Host "   $morningTest" -ForegroundColor Red
} else {
    Write-Host "⚠️  WARNING: Unclear result. Check Telegram manually." -ForegroundColor Yellow
}
$checks_total++

Write-Host ""

# ============ STEP 4: Task Scheduler Tasks ============
Write-Host "┌─ STEP 4: Task Scheduler Tasks ──────────────────────────────┐" -ForegroundColor Blue
Write-Host ""

$tasks = @(
    "DSA Bot - Morning (7 AM)",
    "DSA Bot - Afternoon (2 PM)",
    "DSA Bot - Evening (6 PM)",
    "DSA Bot - Night (9 PM)",
    "DSA Bot - Poll (Every 5 min)"
)

$foundTasks = 0
foreach ($task in $tasks) {
    $existingTask = Get-ScheduledTask -TaskName $task -ErrorAction SilentlyContinue
    if ($existingTask) {
        Write-Host "✅ Found: $task (State: $($existingTask.State))" -ForegroundColor Green
        $foundTasks++
    } else {
        Write-Host "❌ Missing: $task" -ForegroundColor Red
    }
}
$checks_passed += $foundTasks
$checks_total += $tasks.Count

Write-Host ""

# ============ STEP 5: Feature Verification ============
Write-Host "┌─ STEP 5: New Features ──────────────────────────────────────┐" -ForegroundColor Blue
Write-Host ""

# Check for Solution button in code
$botContent = Get-Content "$botPath\reminder_bot.py" -Raw
if ($botContent -match '📋 Solution') {
    Write-Host "✅ PASS: 📋 Solution button added" -ForegroundColor Green
    $checks_passed++
} else {
    Write-Host "❌ FAIL: 📋 Solution button not found" -ForegroundColor Red
}
$checks_total++

# Check for generate_solution_preview function
if ($botContent -match 'def generate_solution_preview') {
    Write-Host "✅ PASS: generate_solution_preview function exists" -ForegroundColor Green
    $checks_passed++
} else {
    Write-Host "❌ FAIL: generate_solution_preview function missing" -ForegroundColor Red
}
$checks_total++

# Check for solution action handler
if ($botContent -match 'action == "solution"') {
    Write-Host "✅ PASS: Solution action handler exists" -ForegroundColor Green
    $checks_passed++
} else {
    Write-Host "❌ FAIL: Solution action handler missing" -ForegroundColor Red
}
$checks_total++

Write-Host ""

# ============ SUMMARY ============
Write-Host "┌─ VERIFICATION SUMMARY ──────────────────────────────────────┐" -ForegroundColor Blue
Write-Host ""

$percentage = [Math]::Round(($checks_passed / $checks_total) * 100, 0)

Write-Host "Results: $checks_passed/$checks_total checks passed ($percentage%)" -ForegroundColor Cyan
Write-Host ""

if ($checks_passed -eq $checks_total) {
    Write-Host "🎉 ALL CHECKS PASSED! Your setup is ready to deploy." -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Green
    Write-Host "  1. Check Telegram for the morning mode test message" -ForegroundColor Gray
    Write-Host "  2. Verify 7 buttons appear on problem messages (including 📋 Solution)" -ForegroundColor Gray
    Write-Host "  3. Enable all 5 Task Scheduler tasks" -ForegroundColor Gray
    Write-Host "  4. Tasks will run automatically at scheduled times" -ForegroundColor Gray
} elseif ($checks_passed -ge ($checks_total - 3)) {
    Write-Host "⚠️  MOSTLY WORKING - Minor issues to fix:" -ForegroundColor Yellow
    Write-Host "  • Review the ❌ items above" -ForegroundColor Yellow
    Write-Host "  • Create missing Task Scheduler tasks" -ForegroundColor Yellow
} else {
    Write-Host "❌ SETUP INCOMPLETE - Critical issues found:" -ForegroundColor Red
    Write-Host "  • Fix the ❌ items above before deploying" -ForegroundColor Red
    Write-Host "  • Check Python, .env, and file paths" -ForegroundColor Red
}

Write-Host ""
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
