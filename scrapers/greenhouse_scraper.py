"""
Greenhouse Platform Scraper

Scrapes job postings from Greenhouse-based career sites.
Many companies use Greenhouse as their ATS (Applicant Tracking System).
"""

import json
from scrapers.base_scraper import BaseScraper


class GreenhouseScraper(BaseScraper):
    """Scraper for Greenhouse-based career sites."""

    def scrape(self):
        """
        Scrape jobs from Greenhouse API.

        Returns:
            list: List of job dictionaries
        """
        self.log("Starting Greenhouse scrape...")

        # Greenhouse API pattern
        # Option 1: Try API endpoint
        greenhouse_id = self.config.get('greenhouse_id')

        if not greenhouse_id:
            self.log("No greenhouse_id configured, attempting to extract from URL", "WARNING")
            # Try to extract from URL patterns like:
            # https://boards.greenhouse.io/company
            # https://job-boards.greenhouse.io/company
            # https://company.com/careers (needs greenhouse_id in config)
            self.log("Please add 'greenhouse_id' to company config", "ERROR")
            return []

        # Try the JSON API endpoint
        api_url = f"https://boards-api.greenhouse.io/v1/boards/{greenhouse_id}/jobs"

        self.log(f"Fetching from Greenhouse API: {api_url}")
        response = self.make_request(api_url)

        if not response:
            # Try alternative endpoint
            alt_url = f"https://boards.greenhouse.io/embed/job_board/jobs?for={greenhouse_id}"
            self.log(f"Trying alternative endpoint: {alt_url}")
            response = self.make_request(alt_url)

            if not response:
                self.log("Failed to fetch from Greenhouse API", "ERROR")
                return []

        try:
            data = response.json()
        except json.JSONDecodeError as e:
            self.log(f"Failed to parse JSON response: {e}", "ERROR")
            return []

        # Parse jobs from Greenhouse response
        jobs = []
        job_list = data.get('jobs', [])

        if not job_list:
            self.log(f"No jobs found in response. Keys: {data.keys()}", "WARNING")
            return []

        for job in job_list:
            try:
                # Extract location
                location = job.get('location', {})
                if isinstance(location, dict):
                    location_str = location.get('name', 'Not specified')
                else:
                    location_str = str(location) if location else 'Not specified'

                # Extract department
                departments = job.get('departments', [])
                if departments and isinstance(departments, list):
                    department = departments[0].get('name', 'Not specified')
                else:
                    department = 'Not specified'

                # Check if remote
                remote = 'No'
                if 'remote' in location_str.lower() or job.get('remote', False):
                    remote = 'Yes'

                job_info = {
                    'title': job.get('title', 'Not specified'),
                    'department': department,
                    'location': location_str,
                    'posting_date': job.get('updated_at', job.get('created_at', 'Not specified')),
                    'remote': remote,
                    'region': 'Not specified',
                    'url': job.get('absolute_url', '')
                }

                jobs.append(job_info)

            except Exception as e:
                self.log(f"Error parsing job: {e}", "WARNING")
                continue

        self.log(f"Completed: {len(jobs)} jobs scraped")
        return jobs
