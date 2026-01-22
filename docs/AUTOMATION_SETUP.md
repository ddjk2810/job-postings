# Veeva Jobs Scraper - Automation Setup Guide

This guide explains how to set up automated daily scraping of Veeva job postings.

## Overview

The automation system consists of:
- **veeva_scraper.py** - Scrapes job postings from Veeva careers page
- **track_new_jobs.py** - Detects new jobs compared to previous run
- **consolidate_jobs.py** - Creates a consolidated view of jobs
- **run_daily_scrape.py** - Master script that runs all three in sequence
- **run_daily_scrape.bat** - Windows batch file for Task Scheduler

## What Gets Created Daily

Each day, the system generates:
1. `veeva_jobs_YYYY-MM-DD.csv` - All current job postings
2. `veeva_jobs_new_YYYY-MM-DD.csv` - Only NEW jobs (not in previous run)
3. `veeva_jobs_consolidated_YYYY-MM-DD.csv` - Consolidated view with duplicates merged
4. `jobs_tracking.json` - Internal tracking database
5. Log file in `logs/` folder (if using Task Scheduler)

## Setup Instructions

### Step 1: Create Logs Directory

```bash
mkdir logs
```

### Step 2: Test the Daily Script Manually

Before setting up automation, test the script:

```bash
python run_daily_scrape.py
```

This will:
- Scrape current jobs
- Create the tracking database (first run only)
- Generate all CSV files

### Step 3: Set Up Windows Task Scheduler

#### Option A: Using Task Scheduler GUI

1. **Open Task Scheduler**
   - Press `Win + R`
   - Type `taskschd.msc` and press Enter

2. **Create a New Task**
   - Click "Create Basic Task" in the right panel
   - Name: `Veeva Jobs Daily Scraper`
   - Description: `Scrapes Veeva job postings daily and detects new jobs`

3. **Set Trigger**
   - Choose "Daily"
   - Set start date and time (recommended: early morning, e.g., 6:00 AM)
   - Set recurrence: Every 1 day

4. **Set Action**
   - Choose "Start a program"
   - Program/script: `C:\Users\HenryLuo\my-new-project\run_daily_scrape.bat`
   - Start in: `C:\Users\HenryLuo\my-new-project`

5. **Finish**
   - Review settings and click Finish
   - Optional: Check "Open the Properties dialog" to configure advanced settings

#### Option B: Using Command Line

Open PowerShell as Administrator and run:

```powershell
$action = New-ScheduledTaskAction -Execute 'C:\Users\HenryLuo\my-new-project\run_daily_scrape.bat' -WorkingDirectory 'C:\Users\HenryLuo\my-new-project'
$trigger = New-ScheduledTaskTrigger -Daily -At 6:00AM
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
Register-ScheduledTask -TaskName "Veeva Jobs Daily Scraper" -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description "Scrapes Veeva job postings daily and detects new jobs"
```

### Step 4: Advanced Task Scheduler Settings (Optional)

After creating the task, you can modify these settings:
1. Right-click the task → Properties
2. **General** tab:
   - ✓ Run whether user is logged on or not
   - ✓ Run with highest privileges (if needed)
3. **Conditions** tab:
   - ✓ Start the task only if the computer is on AC power (uncheck if laptop)
   - ✓ Wake the computer to run this task
4. **Settings** tab:
   - ✓ Allow task to be run on demand
   - ✓ If the task fails, restart every: 1 hour

## How It Works

### First Run
- Scrapes all jobs
- Saves to tracking database
- Creates full CSV files
- No "new jobs" file (baseline established)

### Subsequent Runs
- Scrapes all current jobs
- Compares with tracking database
- Identifies new jobs
- Creates all three CSV files
- Updates tracking database

## File Organization

Recommended folder structure:
```
my-new-project/
├── veeva_scraper.py
├── track_new_jobs.py
├── consolidate_jobs.py
├── run_daily_scrape.py
├── run_daily_scrape.bat
├── requirements.txt
├── jobs_tracking.json (auto-created)
├── logs/
│   └── scrape_2026-01-03.log
└── veeva_jobs_*.csv (daily files)
```

## Monitoring

### Check if Task is Running
1. Open Task Scheduler
2. Find "Veeva Jobs Daily Scraper"
3. Check "Last Run Time" and "Last Run Result"

### View Logs
Check the `logs/` folder for daily log files showing the scraper output.

### Manual Run
To run the scraper manually at any time:
```bash
python run_daily_scrape.py
```

## Troubleshooting

### Task doesn't run
- Check Task Scheduler → Task History
- Verify Python is in system PATH
- Check "Last Run Result" code:
  - 0x0 = Success
  - 0x1 = Failed

### No new jobs detected
- This is normal if Veeva hasn't posted new jobs
- Check `jobs_tracking.json` was created
- Verify previous run completed successfully

### Script errors
- Check log files in `logs/` folder
- Run manually to see errors: `python run_daily_scrape.py`
- Verify internet connection

## Customization

### Change Schedule
Edit the trigger in Task Scheduler to run:
- Multiple times per day
- Weekly instead of daily
- At different times

### Notification on New Jobs
To get notified of new jobs, you could:
1. Add email notification code to `track_new_jobs.py`
2. Use Task Scheduler's "Send an email" action (deprecated but may work)
3. Integrate with services like Pushover, Telegram, or Slack

### Data Retention
To automatically clean up old CSV files:
- Add cleanup code to `run_daily_scrape.py`
- Keep only last 30 days of data
- Archive old files to separate folder

## Support

If you encounter issues:
1. Check log files
2. Run scripts manually to see errors
3. Verify all dependencies are installed: `pip install -r requirements.txt`
