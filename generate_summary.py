#!/usr/bin/env python3
"""
Generate a markdown summary of new job postings for GitHub Issues/notifications.
"""

import argparse
import csv
import os
from datetime import datetime
from pathlib import Path


def get_seniority_level(title):
    """Categorize job by seniority level."""
    title_lower = title.lower()

    if any(x in title_lower for x in ['chief', ' vp ', 'vp,', 'vice president']):
        return 1, 'C-Level / VP'
    elif 'director' in title_lower:
        return 2, 'Director'
    elif any(x in title_lower for x in ['principal', 'distinguished', 'architect']):
        return 3, 'Principal / Architect'
    elif any(x in title_lower for x in ['staff', 'senior', ' sr ', 'sr.', 'lead']):
        return 4, 'Senior / Staff / Lead'
    elif 'manager' in title_lower:
        return 5, 'Manager'
    elif any(x in title_lower for x in ['associate', 'junior', 'intern', ' i ', ' 1 ']):
        return 7, 'Associate / Junior / Intern'
    else:
        return 6, 'Mid-Level'


def load_company_config(fund=None):
    """Load company configuration to get display names, optionally filtered by fund."""
    import json
    config_path = Path('companies_config.json')
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = json.load(f)
            companies = config.get('companies', [])
            if fund:
                companies = [c for c in companies if c.get('fund') == fund]
            return {c['slug']: c['name'] for c in companies}
    return {}


def generate_summary(date_override=None, fund=None):
    """Generate markdown summary of new jobs."""
    today = date_override or datetime.now().strftime('%Y-%m-%d')
    companies_dir = Path('companies')

    company_names = load_company_config(fund=fund)

    all_new_jobs = []
    company_counts = {}
    report_date = None

    # Collect all new jobs
    for company_dir in companies_dir.iterdir():
        if not company_dir.is_dir():
            continue

        # Skip companies not in the filtered config (fund filtering)
        if fund and company_dir.name not in company_names:
            continue

        # Only use today's new jobs file — no fallback to stale files
        new_jobs_file = company_dir / f"{company_dir.name}_jobs_new_{today}.csv"
        if not new_jobs_file.exists():
            continue

        # Extract date from filename for report
        if report_date is None:
            import re
            match = re.search(r'_new_(\d{4}-\d{2}-\d{2})\.csv', new_jobs_file.name)
            if match:
                report_date = match.group(1)

        company_slug = company_dir.name
        company_name = company_names.get(company_slug, company_slug.title())

        with open(new_jobs_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            jobs = list(reader)

        if jobs:
            company_counts[company_name] = len(jobs)
            for job in jobs:
                job['company'] = company_name
                all_new_jobs.append(job)

    if not all_new_jobs:
        return None, "No new jobs found today."

    # Use report_date for display, fall back to today
    display_date = report_date or today

    # Sort by seniority
    all_new_jobs.sort(key=lambda x: (get_seniority_level(x.get('title', ''))[0], x.get('company', '')))

    # Generate markdown
    lines = []
    lines.append(f"# New Job Postings - {display_date}\n")
    lines.append(f"**Total new jobs: {len(all_new_jobs)}** across {len(company_counts)} companies\n")

    # Summary by company
    lines.append("## Summary by Company\n")
    lines.append("| Company | New Jobs |")
    lines.append("|---------|----------|")
    for company, count in sorted(company_counts.items(), key=lambda x: -x[1]):
        lines.append(f"| {company} | {count} |")
    lines.append("")

    # Jobs by seniority
    current_level = None
    for job in all_new_jobs:
        level_num, level_name = get_seniority_level(job.get('title', ''))

        if level_name != current_level:
            current_level = level_name
            lines.append(f"\n## {level_name}\n")
            lines.append("| Company | Title | Location |")
            lines.append("|---------|-------|----------|")

        title = job.get('title', 'Unknown')
        company = job.get('company', 'Unknown')
        location = job.get('location', 'Not specified')
        url = job.get('url', '')

        # Truncate long fields
        if len(title) > 60:
            title = title[:57] + "..."
        if len(location) > 40:
            location = location[:37] + "..."

        if url:
            lines.append(f"| {company} | [{title}]({url}) | {location} |")
        else:
            lines.append(f"| {company} | {title} | {location} |")

    # Engineering highlights
    eng_jobs = [j for j in all_new_jobs if any(x in j.get('title', '').lower()
                for x in ['engineer', 'developer', 'software', 'architect', 'sre', 'devops', 'mlops'])]

    if eng_jobs:
        lines.append(f"\n---\n")
        lines.append(f"## Engineering Roles Highlight ({len(eng_jobs)} positions)\n")

        senior_eng = [j for j in eng_jobs if get_seniority_level(j.get('title', ''))[0] <= 4]
        if senior_eng[:10]:  # Top 10
            lines.append("### Senior+ Engineering\n")
            for job in senior_eng[:10]:
                title = job.get('title', '')
                company = job.get('company', '')
                url = job.get('url', '')
                location = job.get('location', 'Remote')
                if url:
                    lines.append(f"- **{company}**: [{title}]({url}) - {location}")
                else:
                    lines.append(f"- **{company}**: {title} - {location}")

    # Product Management highlights
    pm_keywords = ['product manager', 'product owner', 'product management', 'product strategy',
                   'product operations', 'group product', 'head of product', 'vp of product', 'product lead']
    pm_jobs = [j for j in all_new_jobs if any(x in j.get('title', '').lower() for x in pm_keywords)]

    if pm_jobs:
        lines.append(f"\n---\n")
        lines.append(f"## Product Management Roles Highlight ({len(pm_jobs)} positions)\n")

        senior_pm = [j for j in pm_jobs if get_seniority_level(j.get('title', ''))[0] <= 4]
        other_pm = [j for j in pm_jobs if get_seniority_level(j.get('title', ''))[0] >= 5]

        if senior_pm[:10]:
            lines.append("### Senior+ Product Management\n")
            for job in senior_pm[:10]:
                title = job.get('title', '')
                company = job.get('company', '')
                url = job.get('url', '')
                location = job.get('location', 'Remote')
                if url:
                    lines.append(f"- **{company}**: [{title}]({url}) - {location}")
                else:
                    lines.append(f"- **{company}**: {title} - {location}")

        if other_pm[:10]:
            lines.append("\n### Other Product Roles\n")
            for job in other_pm[:10]:
                title = job.get('title', '')
                company = job.get('company', '')
                url = job.get('url', '')
                location = job.get('location', 'Remote')
                if url:
                    lines.append(f"- **{company}**: [{title}]({url}) - {location}")
                else:
                    lines.append(f"- **{company}**: {title} - {location}")

    # Add company hiring priority insights
    try:
        from generate_company_insights import generate_all_insights, format_insights_markdown
        insights, date_from, date_to = generate_all_insights(fund=fund)
        if insights:
            lines.append(format_insights_markdown(insights, date_from, date_to))
    except Exception as e:
        lines.append(f"\n*Could not generate company insights: {e}*\n")

    summary = '\n'.join(lines)
    fund_label = f" [{fund.upper()} Fund]" if fund else ""
    title = f"New Jobs{fund_label}: {display_date} - {len(all_new_jobs)} positions"

    return title, summary


def main():
    parser = argparse.ArgumentParser(description='Generate job posting summary')
    parser.add_argument('--fund', choices=['partners', 'scf'],
                        help='Filter companies by fund (partners or scf)')
    args = parser.parse_args()

    title, summary = generate_summary(fund=args.fund)

    if title is None:
        print("No new jobs to report.")
        return

    # Fund-suffix output files to avoid collisions
    suffix = f"_{args.fund}" if args.fund else ""
    summary_file = f"job_summary{suffix}.md"
    title_file = f"job_summary_title{suffix}.txt"

    # Write to file for GitHub Actions to pick up
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(summary)

    # Write title separately
    with open(title_file, 'w', encoding='utf-8') as f:
        f.write(title)

    print(f"Summary generated: {title}")
    print(f"Total characters: {len(summary)}")


if __name__ == "__main__":
    main()
