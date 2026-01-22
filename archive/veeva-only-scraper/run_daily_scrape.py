#!/usr/bin/env python3
"""
Daily Veeva Jobs Scraper

Master script that:
1. Scrapes current job postings from Veeva
2. Detects new jobs compared to previous run
3. Creates consolidated view
4. Tracks daily job count history
5. Saves all results with timestamps

This script is designed to be run daily via Task Scheduler.
"""

import subprocess
import sys
from datetime import datetime


def run_script(script_name, description):
    """
    Run a Python script and handle errors.

    Args:
        script_name (str): Name of the script to run
        description (str): Description of what the script does

    Returns:
        bool: True if successful, False otherwise
    """
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"{'='*60}")

    try:
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        print(result.stdout)

        if result.stderr:
            print("Errors/Warnings:")
            print(result.stderr)

        if result.returncode != 0:
            print(f"⚠ {script_name} exited with code {result.returncode}")
            return False

        return True

    except subprocess.TimeoutExpired:
        print(f"⚠ {script_name} timed out after 5 minutes")
        return False
    except Exception as e:
        print(f"⚠ Error running {script_name}: {e}")
        return False


def main():
    """Run the daily job scraping workflow."""
    start_time = datetime.now()
    print("\n" + "="*60)
    print("VEEVA DAILY JOB SCRAPER - AUTOMATED RUN")
    print("="*60)
    print(f"Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # Step 1: Scrape current jobs
    if not run_script('veeva_scraper.py', 'Scraping Veeva job postings'):
        print("\n⚠ Scraping failed. Aborting workflow.")
        sys.exit(1)

    # Step 2: Detect new jobs
    if not run_script('track_new_jobs.py', 'Detecting new job postings'):
        print("\n⚠ New job detection failed, but continuing...")

    # Step 3: Create consolidated view
    if not run_script('consolidate_jobs.py', 'Creating consolidated job view'):
        print("\n⚠ Consolidation failed, but continuing...")

    # Step 4: Track daily job counts
    if not run_script('track_job_counts.py', 'Tracking daily job count history'):
        print("\n⚠ Job count tracking failed, but continuing...")

    # Summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print("\n" + "="*60)
    print("DAILY SCRAPE COMPLETED")
    print("="*60)
    print(f"Finished at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Duration: {duration:.1f} seconds")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
