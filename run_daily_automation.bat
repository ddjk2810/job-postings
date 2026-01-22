@echo off
REM Daily Job Tracker Automation - Windows Batch File
REM This runs the complete daily workflow: scrape, track, consolidate

cd /d "%~dp0"

REM Create logs directory if it doesn't exist
if not exist "logs" mkdir logs

REM Run the daily automation with logging
python run_daily_automation.py > logs\automation_%date:~-4,4%-%date:~-10,2%-%date:~-7,2%.log 2>&1

REM Exit with the same code as the Python script
exit /b %ERRORLEVEL%
