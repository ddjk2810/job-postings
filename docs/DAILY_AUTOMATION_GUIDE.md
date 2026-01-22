# Daily Automation Setup Guide

Complete guide to automating the daily job scraping and tracking workflow.

---

## 📋 What Gets Automated

When you run the daily automation, it executes this workflow:

### Step 1: Scrape All Companies (~3-4 minutes)
- Runs `scrape_all_companies.py`
- Scrapes all 16 working companies
- Creates daily CSV files for each company
- Saves to `companies/[company]/[company]_jobs_YYYY-MM-DD.csv`

### Step 2: Track New Jobs (per company)
- Runs `track_new_jobs.py` for each company
- Compares today's jobs with previous run
- Identifies NEW job postings
- Saves to `companies/[company]/[company]_jobs_new_YYYY-MM-DD.csv`
- Updates tracking database

### Step 3: Consolidate Jobs (per company)
- Runs `consolidate_jobs.py` for each company
- Merges duplicate job titles with different locations
- Shows openings count per title
- Saves to `companies/[company]/[company]_jobs_consolidated_YYYY-MM-DD.csv`

### Step 4: Track Job Counts (per company)
- Runs `track_job_counts.py` for each company
- Records daily job count
- Updates historical trends
- Saves to `companies/[company]/job_count_history.csv`

---

## 🚀 Quick Start

### Option 1: Run Manually (Test First)

```bash
# Test the complete workflow
python run_daily_automation.py
```

This will:
- Take 3-5 minutes to complete
- Output progress to console
- Show summary at the end

### Option 2: Set Up Windows Task Scheduler (Recommended)

Follow the instructions below to run automatically every day.

---

## 🔧 Windows Task Scheduler Setup

### Method 1: Using GUI (Easiest)

#### Step 1: Open Task Scheduler
1. Press `Win + R`
2. Type `taskschd.msc`
3. Press Enter

#### Step 2: Create New Task
1. Click **"Create Basic Task"** in right panel
2. Name: `Daily Job Scraper`
3. Description: `Scrapes job postings from 16 companies and tracks changes`
4. Click **Next**

#### Step 3: Set Trigger (When to Run)
1. Choose **"Daily"**
2. Click **Next**
3. Set start date: **Today's date**
4. Set time: **6:00 AM** (or your preferred time)
5. Recur every: **1 days**
6. Click **Next**

**Tip:** Run early morning (6 AM) so results are ready when you start work

#### Step 4: Set Action (What to Run)
1. Choose **"Start a program"**
2. Click **Next**
3. Program/script: Browse to `run_daily_automation.bat`
   - Full path: `C:\Users\HenryLuo\my-new-project\run_daily_automation.bat`
4. Start in: `C:\Users\HenryLuo\my-new-project`
5. Click **Next**

#### Step 5: Finish
1. Review settings
2. Check ☑ **"Open the Properties dialog when I click Finish"**
3. Click **Finish**

#### Step 6: Configure Advanced Settings (Important!)
In the Properties dialog that opens:

**General Tab:**
- ☑ Run whether user is logged on or not
- ☑ Run with highest privileges

**Conditions Tab:**
- ☑ Start the task only if the computer is on AC power (uncheck if laptop)
- ☑ Wake the computer to run this task

**Settings Tab:**
- ☑ Allow task to be run on demand
- ☑ Run task as soon as possible after a scheduled start is missed
- ☑ If the task fails, restart every: **1 hour**
- ☐ Stop the task if it runs longer than: **2 hours**

Click **OK** to save.

---

### Method 2: Using PowerShell (Advanced)

Run PowerShell as Administrator and execute:

```powershell
$action = New-ScheduledTaskAction `
    -Execute 'C:\Users\HenryLuo\my-new-project\run_daily_automation.bat' `
    -WorkingDirectory 'C:\Users\HenryLuo\my-new-project'

$trigger = New-ScheduledTaskTrigger -Daily -At 6:00AM

$principal = New-ScheduledTaskPrincipal `
    -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType Interactive `
    -RunLevel Highest

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Hours 1)

Register-ScheduledTask `
    -TaskName "Daily Job Scraper" `
    -Action $action `
    -Trigger $trigger `
    -Principal $principal `
    -Settings $settings `
    -Description "Scrapes 16 companies and tracks job changes daily"
```

---

## 📊 What You Get Each Day

### For Each Company (16 total):

```
companies/veeva/
├── veeva_jobs_2026-01-03.csv              # All jobs today
├── veeva_jobs_new_2026-01-03.csv          # NEW jobs only
├── veeva_jobs_consolidated_2026-01-03.csv # Deduplicated view
├── jobs_tracking.json                      # Internal tracking DB
└── job_count_history.csv                   # Historical trends

companies/procore/
├── procore_jobs_2026-01-03.csv
├── procore_jobs_new_2026-01-03.csv
├── procore_jobs_consolidated_2026-01-03.csv
├── jobs_tracking.json
└── job_count_history.csv

... (14 more companies)
```

### Summary Reports:
- `scraping_summary_2026-01-03.json` - Daily scraping results
- `logs/automation_2026-01-03.log` - Full automation log

---

## 📁 File Organization Over Time

```
companies/veeva/
├── veeva_jobs_2026-01-03.csv
├── veeva_jobs_2026-01-04.csv
├── veeva_jobs_2026-01-05.csv
├── veeva_jobs_new_2026-01-04.csv         # Only if new jobs found
├── veeva_jobs_new_2026-01-05.csv
├── veeva_jobs_consolidated_2026-01-03.csv
├── veeva_jobs_consolidated_2026-01-04.csv
├── job_count_history.csv                 # Growing history file
└── jobs_tracking.json                     # Updated daily
```

---

## 🔍 Monitoring Your Automation

### Check if Task is Running

**Method 1: Task Scheduler**
1. Open Task Scheduler
2. Find "Daily Job Scraper"
3. Check columns:
   - **Last Run Time**: When it last executed
   - **Last Run Result**: Success (0x0) or error code
   - **Next Run Time**: When it will run next
   - **Status**: Ready, Running, or Disabled

**Method 2: Log Files**
Check the `logs/` folder for daily log files:
```bash
# View today's log
cat logs/automation_2026-01-03.log

# Check if it ran successfully
grep "SUCCESS" logs/automation_2026-01-03.log
```

### Understand Status Codes

| Code | Meaning |
|------|---------|
| 0x0 | Success |
| 0x1 | Failed |
| 0x41301 | Task is currently running |
| 0x41303 | Task has not yet run |

---

## 🎯 What Happens on First Run vs. Daily Runs

### First Run (Today)
- Scrapes all 16 companies
- Creates tracking databases
- **No "new jobs" files** (establishes baseline)
- Creates initial `job_count_history.csv`

**Output:**
- `[company]_jobs_2026-01-03.csv` for each company
- `jobs_tracking.json` for each company
- `job_count_history.csv` for each company

### Second Run (Tomorrow)
- Scrapes all 16 companies again
- Compares with yesterday's data
- **Creates "new jobs" CSV** if any new postings found
- Updates job count history

**Output:**
- `[company]_jobs_2026-01-04.csv` for each company
- `[company]_jobs_new_2026-01-04.csv` (only if new jobs exist)
- Updated `jobs_tracking.json`
- Updated `job_count_history.csv` (adds new row)

### Daily Runs (Ongoing)
- Continuous tracking of job changes
- Growing historical trends
- Easy to spot hiring patterns

---

## 📧 Optional: Email Notifications

### When New Jobs Are Found

You can enhance the system to send email when new jobs are detected.

**Option 1: Add to `track_new_jobs.py`**

```python
# Add at the top
import smtplib
from email.message import EmailMessage

def send_email_alert(company, new_job_count):
    msg = EmailMessage()
    msg['Subject'] = f'New Jobs Alert: {company} has {new_job_count} new postings'
    msg['From'] = 'your-email@gmail.com'
    msg['To'] = 'your-email@gmail.com'
    msg.set_content(f'{company} posted {new_job_count} new jobs today!')

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login('your-email@gmail.com', 'your-app-password')
        smtp.send_message(msg)
```

**Option 2: Use Task Scheduler Email (Deprecated but may work)**
In Task Scheduler → Actions → Send an Email (if available)

**Option 3: Use External Service**
- IFTTT
- Zapier
- Microsoft Power Automate

---

## 🛠️ Troubleshooting

### Task Doesn't Run

**Check 1: Verify Python Path**
```bash
where python
# Should show: C:\Users\HenryLuo\AppData\Local\Python\...
```

**Check 2: Test Batch File Manually**
```bash
cd C:\Users\HenryLuo\my-new-project
run_daily_automation.bat
```

**Check 3: Check Task Scheduler History**
1. Open Task Scheduler
2. View → Show Hidden Tasks
3. Right-click "Daily Job Scraper"
4. Select "Properties"
5. Go to "History" tab
6. Review recent runs

**Check 4: Review Log Files**
```bash
# Check latest log
cat logs/automation_*.log | tail -50
```

### Task Runs But Fails

**Check Log File:**
```bash
# Find errors in log
grep "ERROR" logs/automation_2026-01-03.log
```

**Common Issues:**
1. **Chrome/ChromeDriver not found**
   - Headless scrapers may fail
   - Reinstall: `pip install selenium webdriver-manager`

2. **Network issues**
   - Check internet connection
   - May need to retry

3. **Company website changed**
   - Scraper may need updates
   - Check which company failed in logs

### No New Jobs Detected

**This is normal!** Companies don't post new jobs every day.

Check the log:
```
  New jobs detected: 0
  No new jobs since last run
```

This means the system is working correctly - just no new postings today.

---

## 🗂️ Data Cleanup (Optional)

### Automatically Delete Old Files

To prevent disk space issues, you can clean up old files:

**Add to automation script:**
```python
# Delete CSV files older than 30 days
import glob
from datetime import datetime, timedelta

cutoff = datetime.now() - timedelta(days=30)
for csv_file in glob.glob('companies/*/*_jobs_*.csv'):
    # Parse date from filename
    # Delete if older than cutoff
```

**Or use Windows Task Scheduler:**
Create a weekly task to clean up old files.

---

## 📊 Analyzing Your Data

### View Historical Trends

```python
import pandas as pd

# Load history for a company
df = pd.read_csv('companies/veeva/job_count_history.csv')

# Plot trends
df['date'] = pd.to_datetime(df['date'])
df.plot(x='date', y='total_jobs', title='Veeva Job Count Over Time')
```

### Aggregate All Companies

```python
import pandas as pd
from pathlib import Path

# Combine all company histories
all_data = []
for company_dir in Path('companies').iterdir():
    history_file = company_dir / 'job_count_history.csv'
    if history_file.exists():
        df = pd.read_csv(history_file)
        df['company'] = company_dir.name
        all_data.append(df)

combined = pd.concat(all_data)
# Now analyze across all companies
```

---

## 🎉 You're All Set!

Once Task Scheduler is set up:

1. **Runs automatically** every day at 6 AM
2. **No manual intervention** needed
3. **Check results** anytime in `companies/` folder
4. **Monitor logs** in `logs/` folder
5. **Review new jobs** in `*_new_*.csv` files

### Daily Workflow:
1. Wake up
2. Check `companies/*/[company]_jobs_new_YYYY-MM-DD.csv`
3. See which companies posted new jobs
4. Apply to interesting positions!

---

## 📝 Quick Reference

| Action | Command |
|--------|---------|
| Run manually | `python run_daily_automation.py` |
| Test scraping only | `python scrape_all_companies.py` |
| Track single company | `python track_new_jobs.py veeva` |
| View logs | `cat logs/automation_*.log` |
| Check Task Scheduler | `taskschd.msc` |

---

**The automation is ready! Set it up once and let it run forever.** 🚀
