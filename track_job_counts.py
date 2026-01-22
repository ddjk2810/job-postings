#!/usr/bin/env python3
"""
Job Count Tracker (Multi-Company Version)

Tracks the number of active job postings each day and maintains a historical log.
Can be run for a specific company or all companies.
"""

import csv
import os
import sys
from datetime import datetime
from collections import defaultdict
from pathlib import Path


def count_jobs_by_department(jobs_file):
    """
    Count jobs by department from the daily CSV file.

    Args:
        jobs_file (Path): Path to the jobs CSV file

    Returns:
        dict: Dictionary with department counts and total
    """
    if not jobs_file.exists():
        return None

    department_counts = defaultdict(int)
    total = 0

    with open(jobs_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            dept = row.get('department', 'Unknown')
            department_counts[dept] += 1
            total += 1

    return {
        'total': total,
        'by_department': dict(department_counts)
    }


def save_daily_count(history_file, date, total_count, department_counts):
    """
    Save today's job count to the history file.

    Args:
        history_file (Path): Path to the history CSV file
        date (str): Date in YYYY-MM-DD format
        total_count (int): Total number of jobs
        department_counts (dict): Counts by department
    """
    # Check if file exists
    file_exists = history_file.exists()

    # Load existing data if file exists
    if file_exists:
        existing_data = []
        with open(history_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            existing_data = [row for row in reader if row['date'] != date]

        # Rewrite file with existing data (excluding today's date if present)
        with open(history_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['date', 'total_jobs', 'top_departments']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(existing_data)

    # Get top 5 departments
    top_depts = sorted(department_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    top_depts_str = '; '.join([f"{dept}: {count}" for dept, count in top_depts])

    # Append today's count
    with open(history_file, 'a', newline='', encoding='utf-8') as f:
        fieldnames = ['date', 'total_jobs', 'top_departments']
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerow({
            'date': date,
            'total_jobs': total_count,
            'top_departments': top_depts_str
        })

    print(f"  Saved job count for {date}: {total_count} total jobs")


def track_counts_for_company(company_slug):
    """
    Track job counts for a specific company.

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
    jobs_file = company_dir / f"{company_slug}_jobs_{today}.csv"

    if not jobs_file.exists():
        print(f"[ERROR] Today's job file not found: {jobs_file}")
        return False

    print(f"\nTracking job counts for: {company_slug}")
    print("-" * 60)

    # Count today's jobs
    job_data = count_jobs_by_department(jobs_file)

    if not job_data:
        print("  Could not read job data")
        return False

    print(f"  Total jobs: {job_data['total']}")

    # Save to history
    history_file = company_dir / 'job_count_history.csv'
    save_daily_count(
        history_file,
        today,
        job_data['total'],
        job_data['by_department']
    )

    return True


def main():
    """Main function."""
    # Check if company slug is provided as argument
    if len(sys.argv) > 1:
        company_slug = sys.argv[1]
        success = track_counts_for_company(company_slug)
        sys.exit(0 if success else 1)

    # Otherwise, track all companies
    print("Job Count Tracker (Multi-Company)")
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
        success = track_counts_for_company(company_dir.name)
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
