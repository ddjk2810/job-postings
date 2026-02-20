#!/usr/bin/env python3
"""
New Jobs Tracker (Multi-Company Version)

Compares today's job scrape with previous data to identify new job postings.
Can be run for a specific company or all companies.
"""

import csv
import os
import json
import sys
from datetime import datetime
from pathlib import Path


def load_jobs_from_csv(filepath):
    """
    Load job postings from a CSV file.

    Args:
        filepath (Path): Path to CSV file

    Returns:
        tuple: (set of job identifiers, list of job dicts)
    """
    if not filepath.exists():
        return set(), []

    jobs_set = set()
    jobs_list = []

    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Create a unique identifier for each job posting
            job_id = (row.get('title', ''), row.get('department', ''), row.get('location', ''))
            jobs_set.add(job_id)
            jobs_list.append(row)

    return jobs_set, jobs_list


def find_new_jobs(current_jobs, previous_jobs):
    """
    Find jobs that appear in current but not in previous.

    Args:
        current_jobs (set): Set of current job identifiers
        previous_jobs (set): Set of previous job identifiers

    Returns:
        set: Set of new job identifiers
    """
    return current_jobs - previous_jobs


def save_new_jobs_csv(new_job_ids, all_current_jobs, output_file):
    """
    Save new jobs to a CSV file.

    Args:
        new_job_ids (set): Set of new job identifiers
        all_current_jobs (list): List of all current job dictionaries
        output_file (Path): Output filepath
    """
    if not new_job_ids:
        print("  No new jobs found.")
        return

    # Deduplicate: only keep the first row matching each identity tuple
    seen = set()
    new_jobs = []
    for job in all_current_jobs:
        job_id = (job.get('title', ''), job.get('department', ''), job.get('location', ''))
        if job_id in new_job_ids and job_id not in seen:
            seen.add(job_id)
            new_jobs.append(job)

    fieldnames = ['title', 'department', 'location', 'posting_date', 'remote', 'region', 'url']

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(new_jobs)

    print(f"  Saved {len(new_jobs)} new job postings to {output_file}")


def update_tracking_database(company_dir, current_jobs_set):
    """
    Update the tracking database by MERGING current jobs into the cumulative history.
    Jobs are never removed from the tracking DB -- this prevents false "new" alerts
    when a job disappears from a scrape (pagination, site issues) then reappears.

    Args:
        company_dir (Path): Company directory
        current_jobs_set (set): Set of current job identifiers
    """
    db_file = company_dir / 'jobs_tracking.json'

    # Load existing cumulative history
    existing_jobs = set()
    if db_file.exists():
        with open(db_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        existing_jobs = set(tuple(job) for job in data.get('jobs', []))

    # Merge: union of existing + current (never lose a job we've seen before)
    all_seen_jobs = existing_jobs | current_jobs_set

    # Convert set of tuples to list of lists for JSON serialization
    jobs_list = [list(job) for job in all_seen_jobs]

    tracking_data = {
        'last_updated': datetime.now().isoformat(),
        'job_count': len(jobs_list),
        'active_count': len(current_jobs_set),
        'jobs': jobs_list
    }

    with open(db_file, 'w', encoding='utf-8') as f:
        json.dump(tracking_data, f, indent=2)

    new_in_db = len(all_seen_jobs) - len(existing_jobs)
    print(f"  Updated tracking database: {len(all_seen_jobs)} total seen ({len(current_jobs_set)} active, {new_in_db} newly added)")


def find_previous_csv(company_dir, company_slug, today):
    """
    Find the most recent CSV file before today to use as baseline.

    Args:
        company_dir (Path): Company directory
        company_slug (str): Company slug
        today (str): Today's date in YYYY-MM-DD format

    Returns:
        Path or None: Path to the most recent previous CSV file
    """
    import re

    # Look for job files matching pattern {slug}_jobs_{date}.csv
    pattern = re.compile(rf'^{re.escape(company_slug)}_jobs_(\d{{4}}-\d{{2}}-\d{{2}})\.csv$')

    previous_files = []
    for f in company_dir.iterdir():
        match = pattern.match(f.name)
        if match:
            file_date = match.group(1)
            if file_date < today:  # Only files before today
                previous_files.append((file_date, f))

    if not previous_files:
        return None

    # Sort by date descending and return the most recent
    previous_files.sort(key=lambda x: x[0], reverse=True)
    return previous_files[0][1]


def load_tracking_database(company_dir, company_slug=None, today=None):
    """
    Load the tracking database, falling back to most recent CSV if no database exists.

    Args:
        company_dir (Path): Company directory
        company_slug (str): Company slug (needed for CSV fallback)
        today (str): Today's date (needed for CSV fallback)

    Returns:
        set: Set of previously tracked job identifiers
    """
    db_file = company_dir / 'jobs_tracking.json'

    if db_file.exists():
        with open(db_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Convert list of lists back to set of tuples
        jobs_set = set(tuple(job) for job in data.get('jobs', []))
        return jobs_set

    # No tracking database - try to find previous CSV as baseline
    if company_slug and today:
        previous_csv = find_previous_csv(company_dir, company_slug, today)
        if previous_csv:
            print(f"  No tracking database, using previous CSV as baseline: {previous_csv.name}")
            jobs_set, _ = load_jobs_from_csv(previous_csv)
            return jobs_set

    return set()


def track_company(company_slug):
    """
    Track new jobs for a specific company.

    Args:
        company_slug (str): Company slug (folder name)

    Returns:
        bool: True if successful, False otherwise
    """
    company_dir = Path('companies') / company_slug

    if not company_dir.exists():
        print(f"[ERROR] Company directory not found: {company_dir}")
        return False

    today = datetime.now().strftime('%Y-%m-%d')
    today_file = company_dir / f"{company_slug}_jobs_{today}.csv"

    if not today_file.exists():
        print(f"[ERROR] Today's job file not found: {today_file}")
        return False

    print(f"\nTracking new jobs for: {company_slug}")
    print("-" * 60)

    # Load current jobs
    current_jobs_set, current_jobs_list = load_jobs_from_csv(today_file)
    print(f"  Current jobs: {len(current_jobs_set)}")

    # Load previous jobs from tracking database (or fallback to previous CSV)
    previous_jobs_set = load_tracking_database(company_dir, company_slug, today)

    if not previous_jobs_set:
        print("  No previous data found (first run)")
        print("  All current jobs will be saved to tracking database")
        update_tracking_database(company_dir, current_jobs_set)
        return True

    print(f"  Previous jobs: {len(previous_jobs_set)}")

    # Find new jobs
    new_jobs_set = find_new_jobs(current_jobs_set, previous_jobs_set)
    print(f"  New jobs detected: {len(new_jobs_set)}")

    # Save new jobs to CSV
    if new_jobs_set:
        output_file = company_dir / f"{company_slug}_jobs_new_{today}.csv"
        save_new_jobs_csv(new_jobs_set, current_jobs_list, output_file)
    else:
        print("  No new jobs since last run")

    # Update tracking database
    update_tracking_database(company_dir, current_jobs_set)

    return True


def main():
    """Main function."""
    # Check if company slug is provided as argument
    if len(sys.argv) > 1:
        company_slug = sys.argv[1]
        success = track_company(company_slug)
        sys.exit(0 if success else 1)

    # Otherwise, track all companies
    print("New Jobs Tracker (Multi-Company)")
    print("=" * 60)

    companies_dir = Path('companies')
    if not companies_dir.exists():
        print("[ERROR] Companies directory not found")
        sys.exit(1)

    # Get all company directories
    company_dirs = [d for d in companies_dir.iterdir() if d.is_dir()]

    if not company_dirs:
        print("[ERROR] No company directories found")
        sys.exit(1)

    print(f"Found {len(company_dirs)} companies\n")

    # Track each company
    results = []
    for company_dir in company_dirs:
        success = track_company(company_dir.name)
        results.append((company_dir.name, success))

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    successful = [r for r in results if r[1]]
    failed = [r for r in results if not r[1]]

    print(f"Total companies: {len(results)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")

    if failed:
        print(f"\nFailed companies:")
        for company, _ in failed:
            print(f"  - {company}")


if __name__ == "__main__":
    main()
