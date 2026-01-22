#!/usr/bin/env python3
"""
Job Consolidation Script (Multi-Company Version)

Consolidates duplicate job titles with different locations into single rows.
Can be run for a specific company or all companies.
"""

import csv
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path


def consolidate_jobs(input_file):
    """
    Consolidates jobs by title and department, grouping locations.

    Args:
        input_file (Path): Path to the input CSV file

    Returns:
        list: Consolidated job data
    """
    # Read the original CSV
    jobs = []
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        jobs = list(reader)

    if not jobs:
        return []

    # Group jobs by title and department
    grouped = defaultdict(lambda: {
        'locations': [],
        'regions': set(),
        'remote_count': 0,
        'department': ''
    })

    for job in jobs:
        key = (job.get('title', ''), job.get('department', ''))
        grouped[key]['locations'].append(job.get('location', ''))
        grouped[key]['regions'].add(job.get('region', ''))
        grouped[key]['department'] = job.get('department', '')
        if job.get('remote') == 'Yes':
            grouped[key]['remote_count'] += 1

    # Create consolidated job list
    consolidated = []
    for (title, dept), data in grouped.items():
        location_count = len(data['locations'])

        # Sort and consolidate locations
        location_list = sorted(set(data['locations']))

        # Create a more readable locations string
        if location_count <= 3:
            locations_str = '; '.join(location_list)
        else:
            # Show first 3 locations and indicate there are more
            locations_str = '; '.join(location_list[:3]) + f' (and {location_count - 3} more)'

        regions_str = ', '.join(sorted(data['regions']))

        consolidated.append({
            'title': title,
            'department': dept,
            'openings': location_count,
            'locations': locations_str,
            'all_locations': ' | '.join(location_list),  # Full list separated by pipes
            'regions': regions_str,
            'remote_available': 'Yes' if data['remote_count'] > 0 else 'No'
        })

    # Sort by number of openings (descending) and then by title
    consolidated.sort(key=lambda x: (-x['openings'], x['title']))

    return consolidated


def save_consolidated_csv(jobs, output_file):
    """
    Saves consolidated job data to CSV.

    Args:
        jobs (list): Consolidated job data
        output_file (Path): Output filepath
    """
    fieldnames = ['title', 'department', 'openings', 'locations', 'all_locations', 'regions', 'remote_available']

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(jobs)

    print(f"  Consolidated data saved to {output_file}")


def consolidate_company(company_slug):
    """
    Consolidate jobs for a specific company.

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
    input_file = company_dir / f"{company_slug}_jobs_{today}.csv"

    if not input_file.exists():
        print(f"[ERROR] Today's job file not found: {input_file}")
        return False

    print(f"\nConsolidating jobs for: {company_slug}")
    print("-" * 60)

    # Consolidate jobs
    consolidated = consolidate_jobs(input_file)

    if not consolidated:
        print("  No jobs to consolidate")
        return False

    # Get original count
    with open(input_file, 'r', encoding='utf-8') as f:
        original_count = sum(1 for _ in csv.DictReader(f))

    print(f"  Original job postings: {original_count}")
    print(f"  Unique job titles: {len(consolidated)}")
    print(f"  Average openings per title: {original_count/len(consolidated):.1f}")

    # Save consolidated data
    output_file = company_dir / f"{company_slug}_jobs_consolidated_{today}.csv"
    save_consolidated_csv(consolidated, output_file)

    return True


def main():
    """Main function."""
    # Check if company slug is provided as argument
    if len(sys.argv) > 1:
        company_slug = sys.argv[1]
        success = consolidate_company(company_slug)
        sys.exit(0 if success else 1)

    # Otherwise, consolidate all companies
    print("Job Consolidation (Multi-Company)")
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

    # Consolidate each company
    results = []
    for company_dir in company_dirs:
        success = consolidate_company(company_dir.name)
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
