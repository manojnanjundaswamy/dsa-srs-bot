# Setup Windows Task Scheduler for DSA SRS Reminders
# Run this with Admin privileges

$ScriptDir = "d:\Claude_Playground\Job and Interview Helper"
$PythonScript = "$ScriptDir\reminder_bot.py"
$PythonExe = (Get-Command python).Source
$EnvFile = "$ScriptDir\.env"

# Read API key from .env file
$EnvContent = Get-Content $EnvFile -Raw
$ApiKey = $EnvContent -match 'ANTHROPIC_API_KEY=(.+)' | ForEach-Object { $matches[1] }

Write-Host "Setting up 3 daily DSA reminder tasks..." -ForegroundColor Green
Write-Host "Python: $PythonExe"
Write-Host "Script: $PythonScript"

# Task 1: Morning Reminder (12:01 PM)
$TaskName1 = "DSA-SRS-Morning-Reminder"
$Action1 = New-ScheduledTaskAction -Execute $PythonExe -Argument "`"$PythonScript`" --mode morning" -WorkingDirectory $ScriptDir
$Trigger1 = New-ScheduledTaskTrigger -Daily -At "12:01 PM"
Register-ScheduledTask -TaskName $TaskName1 -Action $Action1 -Trigger $Trigger1 -RunLevel Highest -Description "DSA SRS Morning Problem Kickoff" -Force | Out-Null
Write-Host "[OK] Task 1: Morning Reminder at 12:01 PM" -ForegroundColor Green

# Task 2: Evening Reminder (7:00 PM)
$TaskName2 = "DSA-SRS-Evening-Reminder"
$Action2 = New-ScheduledTaskAction -Execute $PythonExe -Argument "`"$PythonScript`" --mode evening" -WorkingDirectory $ScriptDir
$Trigger2 = New-ScheduledTaskTrigger -Daily -At "7:00 PM"
Register-ScheduledTask -TaskName $TaskName2 -Action $Action2 -Trigger $Trigger2 -RunLevel Highest -Description "DSA SRS Evening Session Reminder" -Force | Out-Null
Write-Host "[OK] Task 2: Evening Reminder at 7:00 PM" -ForegroundColor Green

# Task 3: Night Summary (10:00 PM)
$TaskName3 = "DSA-SRS-Night-Summary"
$Action3 = New-ScheduledTaskAction -Execute $PythonExe -Argument "`"$PythonScript`" --mode night" -WorkingDirectory $ScriptDir
$Trigger3 = New-ScheduledTaskTrigger -Daily -At "10:00 PM"
Register-ScheduledTask -TaskName $TaskName3 -Action $Action3 -Trigger $Trigger3 -RunLevel Highest -Description "DSA SRS Night Summary" -Force | Out-Null
Write-Host "[OK] Task 3: Night Summary at 10:00 PM" -ForegroundColor Green

Write-Host ""
Write-Host "All tasks ready!" -ForegroundColor Green
Write-Host "Your reminders:" -ForegroundColor Cyan
Write-Host "  - 12:01 PM Morning Problem"
Write-Host "  - 7:00 PM Evening Session"
Write-Host "  - 10:00 PM Night Summary"
