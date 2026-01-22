@echo off
REM Daily Veeva Job Scraper - Windows Batch File
REM This script is designed to be scheduled in Windows Task Scheduler

cd /d "%~dp0"
python run_daily_scrape.py > logs\scrape_%date:~-4,4%-%date:~-10,2%-%date:~-7,2%.log 2>&1
