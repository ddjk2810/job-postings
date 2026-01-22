#!/usr/bin/env python3
"""
Daily Job Tracker Automation

Master script that runs the complete daily workflow:
1. Scrape all companies
2. Track new jobs for each company
3. Create consolidated views
4. Track job count history

Run this script daily via Task Scheduler.
"""

import subprocess
import sys
import json
from datetime import datetime
from pathlib import Path


def run_command(command, description, timeout=600):
    """
    Run a command and capture output.

    Args:
        command (list): Command to run
        description (str): Description for logging
        timeout (int): Timeout in seconds

    Returns:
        bool: True if successful, False otherwise
    """
    print(f"\n{'='*70}")
    print(f"Running: {description}")
    print(f"{'='*70}")

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        print(result.stdout)

        if result.stderr:
            print("Warnings/Errors:")
            print(result.stderr)

        if result.returncode != 0:
            print(f"[WARNING] Command exited with code {result.returncode}")
            return False

        return True

    except subprocess.TimeoutExpired:
        print(f"[ERROR] Command timed out after {timeout} seconds")
        return False
    except Exception as e:
        print(f"[ERROR] Failed to run command: {e}")
        return False


def process_company_tracking(company_slug, company_name):
    """
    Run tracking scripts for a single company.

    Args:
        company_slug (str): Company slug (folder name)
        company_name (str): Company display name

    Returns:
        dict: Results for this company
    """
    company_dir = Path('companies') / company_slug

    if not company_dir.exists():
        print(f"[SKIP] No data folder for {company_name}")
        return {'company': company_name, 'slug': company_slug, 'success': False, 'reason': 'no_data'}

    # Find today's CSV file
    today = datetime.now().strftime('%Y-%m-%d')
    csv_file = company_dir / f"{company_slug}_jobs_{today}.csv"

    if not csv_file.exists():
        print(f"[SKIP] No CSV file for {company_name} today")
        return {'company': company_name, 'slug': company_slug, 'success': False, 'reason': 'no_csv'}

    print(f"\n{'='*70}")
    print(f"Processing: {company_name}")
    print(f"{'='*70}")

    results = {
        'company': company_name,
        'slug': company_slug,
        'success': True,
        'new_jobs': False,
        'consolidated': False,
        'tracked': False
    }

    # Run track_new_jobs for this company
    print(f"\nDetecting new jobs for {company_name}...")
    success = run_command(
        [sys.executable, 'track_new_jobs.py', company_slug],
        f"Track new jobs - {company_name}",
        timeout=60
    )
    results['new_jobs'] = success

    # Run consolidate_jobs for this company
    print(f"\nConsolidating jobs for {company_name}...")
    success = run_command(
        [sys.executable, 'consolidate_jobs.py', company_slug],
        f"Consolidate jobs - {company_name}",
        timeout=60
    )
    results['consolidated'] = success

    # Run track_job_counts for this company
    print(f"\nTracking job counts for {company_name}...")
    success = run_command(
        [sys.executable, 'track_job_counts.py', company_slug],
        f"Track job counts - {company_name}",
        timeout=60
    )
    results['tracked'] = success

    return results


def main():
    """Main automation workflow."""
    start_time = datetime.now()

    print("\n" + "="*70)
    print("DAILY JOB TRACKER AUTOMATION")
    print("="*70)
    print(f"Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)

    # Step 1: Run the main scraper for all companies
    print("\n[STEP 1/2] Scraping all companies...")
    print("="*70)

    scrape_success = run_command(
        [sys.executable, 'scrape_all_companies.py'],
        "Scrape all 16 companies",
        timeout=600  # 10 minutes max
    )

    if not scrape_success:
        print("\n[ERROR] Scraping failed. Aborting workflow.")
        sys.exit(1)

    # Step 2: Run tracking for each company
    print("\n[STEP 2/2] Running tracking for each company...")
    print("="*70)

    # Load company config to get list of enabled companies
    try:
        with open('companies_config.json', 'r') as f:
            config = json.load(f)
        companies = [c for c in config['companies'] if c.get('enabled', True)]
    except Exception as e:
        print(f"[ERROR] Failed to load companies config: {e}")
        sys.exit(1)

    # Process each company
    tracking_results = []
    for company in companies:
        result = process_company_tracking(company['slug'], company['name'])
        tracking_results.append(result)

    # Summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print("\n" + "="*70)
    print("AUTOMATION SUMMARY")
    print("="*70)

    successful_companies = [r for r in tracking_results if r['success']]
    skipped_companies = [r for r in tracking_results if not r['success']]

    print(f"\nTotal companies: {len(companies)}")
    print(f"Processed: {len(successful_companies)}")
    print(f"Skipped: {len(skipped_companies)}")

    if successful_companies:
        print(f"\nProcessed companies:")
        for r in successful_companies:
            status = []
            if r.get('new_jobs'): status.append('new jobs detected')
            if r.get('consolidated'): status.append('consolidated')
            if r.get('tracked'): status.append('counts tracked')

            status_str = ', '.join(status) if status else 'processed'
            print(f"  - {r['company']}: {status_str}")

    if skipped_companies:
        print(f"\nSkipped companies:")
        for r in skipped_companies:
            reason = r.get('reason', 'unknown')
            print(f"  - {r['company']}: {reason}")

    print(f"\nCompleted at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")
    print("="*70)
    print("\n[SUCCESS] Daily automation completed!")


if __name__ == "__main__":
    main()
