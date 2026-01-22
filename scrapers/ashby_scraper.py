"""
Ashby Platform Scraper

Scrapes job postings from Ashby-based career sites.
Ashby is a modern ATS used by many tech startups.
"""

import json
from scrapers.base_scraper import BaseScraper


class AshbyScraper(BaseScraper):
    """Scraper for Ashby-based career sites."""

    def scrape(self):
        """
        Scrape jobs from Ashby API.

        Returns:
            list: List of job dictionaries
        """
        self.log("Starting Ashby scrape...")

        # Ashby company ID
        ashby_id = self.config.get('ashby_id')

        if not ashby_id:
            self.log("No ashby_id configured", "ERROR")
            self.log("Please add 'ashby_id' to company config", "ERROR")
            return []

        # Ashby's public API endpoint
        api_url = f"https://api.ashbyhq.com/posting-api/job-board/{ashby_id}"

        self.log(f"Fetching from Ashby API: {api_url}")

        response = self.make_request(api_url)

        if not response:
            self.log("Failed to fetch from Ashby API", "ERROR")
            return []

        try:
            data = response.json()
        except json.JSONDecodeError as e:
            self.log(f"Failed to parse JSON response: {e}", "ERROR")
            return []

        # Ashby returns jobs in a 'jobs' array
        job_list = data.get('jobs', [])

        if not isinstance(job_list, list):
            self.log(f"Unexpected response format: {type(job_list)}", "ERROR")
            return []

        jobs = []
        for job in job_list:
            try:
                # Extract location
                location = job.get('location', 'Not specified')
                if isinstance(location, dict):
                    location = location.get('name', 'Not specified')

                # Extract department/team
                department = job.get('department', 'Not specified')
                if isinstance(department, dict):
                    department = department.get('name', 'Not specified')

                # Check if remote
                remote = 'No'
                location_str = str(location).lower()
                if 'remote' in location_str:
                    remote = 'Yes'

                # Check for remote flag in job data
                if job.get('isRemote') or job.get('remote'):
                    remote = 'Yes'

                # Build job URL
                job_url = job.get('jobUrl', '')
                if not job_url:
                    job_id = job.get('id', '')
                    if job_id:
                        job_url = f"https://jobs.ashbyhq.com/{ashby_id}/{job_id}"

                job_info = {
                    'title': job.get('title', 'Not specified'),
                    'department': department,
                    'location': location,
                    'posting_date': job.get('publishedAt', job.get('createdAt', 'Not specified')),
                    'remote': remote,
                    'region': 'Not specified',
                    'url': job_url
                }

                jobs.append(job_info)

            except Exception as e:
                self.log(f"Error parsing job: {e}", "WARNING")
                continue

        self.log(f"Completed: {len(jobs)} jobs scraped")
        return jobs
