#!/usr/bin/env python3
"""
Veeva Career Page Web Scraper

This script scrapes job postings from Veeva's career page and saves them to a CSV file.
It extracts job title, department, location, and posting date for all current openings.
"""

import requests
import re
import json
import csv
from datetime import datetime
from collections import Counter


def scrape_veeva_jobs():
    """
    Scrapes job postings from Veeva's career page.

    Returns:
        list: List of dictionaries containing job information
    """
    url = "https://careers.veeva.com/job-search-results/"

    print("Fetching job listings from Veeva careers page...")

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the page: {e}")
        return []

    # Extract the allJobs JavaScript array from the page
    pattern = r'let allJobs = (\[.*?\]);'
    match = re.search(pattern, response.text, re.DOTALL)

    if not match:
        print("Could not find job data on the page.")
        return []

    try:
        jobs_data = json.loads(match.group(1))
        print(f"Successfully extracted {len(jobs_data)} job postings.")
    except json.JSONDecodeError as e:
        print(f"Error parsing job data: {e}")
        return []

    # Process and structure the job data
    jobs = []
    for job in jobs_data:
        # Combine city and country for location
        city = job.get('city', '').strip()
        country = job.get('country', '').strip()
        location = f"{city}, {country}" if city and country else city or country or "Not specified"

        job_info = {
            'title': job.get('job_title', 'Not specified'),
            'department': job.get('team', 'Not specified'),
            'location': location,
            'posting_date': job.get('posted_date', 'Not specified'),
            'remote': 'Yes' if job.get('remote') == 1 else 'No',
            'region': job.get('region', 'Not specified')
        }
        jobs.append(job_info)

    return jobs


def save_to_csv(jobs):
    """
    Saves job data to a CSV file with today's date.

    Args:
        jobs (list): List of job dictionaries

    Returns:
        str: Filename of the created CSV
    """
    today = datetime.now().strftime('%Y-%m-%d')
    filename = f"veeva_jobs_{today}.csv"

    if not jobs:
        print("No jobs to save.")
        return filename

    fieldnames = ['title', 'department', 'location', 'posting_date', 'remote', 'region']

    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(jobs)

        print(f"\nData successfully saved to {filename}")
        return filename
    except IOError as e:
        print(f"Error saving CSV file: {e}")
        return filename


def print_summary(jobs):
    """
    Prints a summary of the job data.

    Args:
        jobs (list): List of job dictionaries
    """
    if not jobs:
        print("\nNo jobs found.")
        return

    print("\n" + "="*60)
    print("VEEVA JOB POSTINGS SUMMARY")
    print("="*60)

    # Total jobs
    print(f"\nTotal Job Postings: {len(jobs)}")

    # Breakdown by department
    departments = Counter(job['department'] for job in jobs)
    print(f"\nBreakdown by Department:")
    print("-" * 60)
    for dept, count in sorted(departments.items(), key=lambda x: x[1], reverse=True):
        print(f"  {dept}: {count}")

    # Additional insights
    locations = Counter(job['location'] for job in jobs)
    print(f"\nTop 5 Locations:")
    print("-" * 60)
    for loc, count in locations.most_common(5):
        print(f"  {loc}: {count}")

    remote_jobs = sum(1 for job in jobs if job['remote'] == 'Yes')
    print(f"\nRemote Positions: {remote_jobs} ({remote_jobs/len(jobs)*100:.1f}%)")
    print("="*60)


def main():
    """Main function to run the scraper."""
    print("Veeva Career Page Web Scraper")
    print("="*60)

    # Scrape jobs
    jobs = scrape_veeva_jobs()

    if jobs:
        # Save to CSV
        save_to_csv(jobs)

        # Print summary
        print_summary(jobs)
    else:
        print("No jobs were scraped. Please check the website structure.")


if __name__ == "__main__":
    main()
