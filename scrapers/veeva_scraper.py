"""
Veeva Custom Scraper

Scrapes job postings from Veeva's career page.
"""

import re
import json
from scrapers.base_scraper import BaseScraper


class VeevaScraper(BaseScraper):
    """Scraper for Veeva career site."""

    def scrape(self):
        """
        Scrape jobs from Veeva careers page.

        Returns:
            list: List of job dictionaries
        """
        self.log("Starting Veeva scrape...")

        response = self.make_request(self.url)

        if not response:
            self.log("Failed to fetch page", "ERROR")
            return []

        # Extract the allJobs JavaScript array from the page
        pattern = r'let allJobs = (\[.*?\]);'
        match = re.search(pattern, response.text, re.DOTALL)

        if not match:
            self.log("Could not find job data on page", "ERROR")
            return []

        try:
            jobs_data = json.loads(match.group(1))
            self.log(f"Successfully extracted {len(jobs_data)} job postings")
        except json.JSONDecodeError as e:
            self.log(f"Error parsing job data: {e}", "ERROR")
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
                'region': job.get('region', 'Not specified'),
                'url': f"https://careers.veeva.com/job/{job.get('slug', '')}" if job.get('slug') else ''
            }
            jobs.append(job_info)

        self.log(f"Completed: {len(jobs)} jobs scraped")
        return jobs
