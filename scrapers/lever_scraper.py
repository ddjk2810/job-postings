"""
Lever Platform Scraper

Scrapes job postings from Lever-based career sites.
Lever is another popular ATS used by many companies.
"""

import json
from scrapers.base_scraper import BaseScraper


class LeverScraper(BaseScraper):
    """Scraper for Lever-based career sites."""

    def scrape(self):
        """
        Scrape jobs from Lever API.

        Returns:
            list: List of job dictionaries
        """
        self.log("Starting Lever scrape...")

        # Lever API pattern
        lever_id = self.config.get('lever_id')

        if not lever_id:
            self.log("No lever_id configured", "ERROR")
            self.log("Please add 'lever_id' to company config (company name in lever URL)", "ERROR")
            return []

        # Lever's public API endpoint
        api_url = f"https://api.lever.co/v0/postings/{lever_id}"

        self.log(f"Fetching from Lever API: {api_url}")

        # Add query parameters
        params = {
            'mode': 'json',
            'skip': 0,
            'limit': 100
        }

        response = self.make_request(api_url, params=params)

        if not response:
            self.log("Failed to fetch from Lever API", "ERROR")
            return []

        try:
            job_list = response.json()
        except json.JSONDecodeError as e:
            self.log(f"Failed to parse JSON response: {e}", "ERROR")
            return []

        if not isinstance(job_list, list):
            self.log(f"Unexpected response format: {type(job_list)}", "ERROR")
            return []

        jobs = []
        for job in job_list:
            try:
                # Extract location
                categories = job.get('categories', {})
                location = categories.get('location', 'Not specified')

                # Extract department/team
                department = categories.get('team', 'Not specified')

                # Extract commitment (Full-time, Part-time, etc.)
                commitment = categories.get('commitment', '')

                # Check if remote
                remote = 'No'
                if 'remote' in str(location).lower() or commitment == 'Remote':
                    remote = 'Yes'

                job_info = {
                    'title': job.get('text', 'Not specified'),
                    'department': department,
                    'location': location,
                    'posting_date': job.get('createdAt', 'Not specified'),
                    'remote': remote,
                    'region': 'Not specified',
                    'url': job.get('hostedUrl', job.get('applyUrl', ''))
                }

                jobs.append(job_info)

            except Exception as e:
                self.log(f"Error parsing job: {e}", "WARNING")
                continue

        self.log(f"Completed: {len(jobs)} jobs scraped")
        return jobs
