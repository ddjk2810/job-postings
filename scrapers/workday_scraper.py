"""
Workday Platform Scraper

Scrapes job postings from Workday-based career sites.
Workday sites use a common API structure that can be accessed directly.
"""

import json
from scrapers.base_scraper import BaseScraper


class WorkdayScraper(BaseScraper):
    """Scraper for Workday-based career sites."""

    def scrape(self):
        """
        Scrape jobs from Workday API.

        Returns:
            list: List of job dictionaries
        """
        self.log("Starting Workday scrape...")

        # Get API base URL from config, or construct it from the main URL
        api_url = self.config.get('api_base')

        if not api_url:
            self.log("No API base URL configured, attempting to construct...", "WARNING")
            # Try to construct API URL from main URL
            # Pattern: https://company.wdX.myworkdayjobs.com/JobBoard
            # API: https://company.wdX.myworkdayjobs.com/wday/cxs/company/JobBoard/jobs
            try:
                parts = self.url.replace('https://', '').split('/')
                domain = parts[0]  # company.wdX.myworkdayjobs.com
                job_board = parts[1] if len(parts) > 1 else ''

                company_subdomain = domain.split('.')[0]
                api_url = f"https://{domain}/wday/cxs/{company_subdomain}/{job_board}/jobs"
                self.log(f"Constructed API URL: {api_url}")
            except Exception as e:
                self.log(f"Failed to construct API URL: {e}", "ERROR")
                return []

        jobs = []
        offset = 0
        limit = 20
        total_fetched = 0

        while True:
            # Workday API typically uses POST with JSON payload
            payload = {
                "appliedFacets": {},
                "limit": limit,
                "offset": offset,
                "searchText": ""
            }

            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            self.log(f"Fetching jobs (offset: {offset})...")
            response = self.make_request(
                api_url,
                method='POST',
                headers=headers,
                json=payload
            )

            if not response:
                self.log("Failed to fetch jobs from API", "ERROR")
                break

            try:
                data = response.json()
            except json.JSONDecodeError as e:
                self.log(f"Failed to parse JSON response: {e}", "ERROR")
                break

            # Extract jobs from response
            job_postings = data.get('jobPostings', [])

            if not job_postings:
                self.log("No more jobs found")
                break

            for job in job_postings:
                try:
                    title = job.get('title', 'Not specified')

                    # Extract location
                    locations = job.get('locationsText', 'Not specified')
                    if isinstance(locations, list):
                        locations = ', '.join(locations)

                    # Extract other fields
                    posted_date = job.get('postedOn', 'Not specified')

                    # Check if remote
                    remote = 'No'
                    if 'remote' in str(locations).lower() or 'remote' in str(title).lower():
                        remote = 'Yes'

                    # Get job URL
                    job_url = ''
                    if 'externalPath' in job:
                        job_url = f"{self.url.rstrip('/')}/{job['externalPath'].lstrip('/')}"

                    job_info = {
                        'title': title,
                        'department': job.get('category', {}).get('label', 'Not specified') if isinstance(job.get('category'), dict) else 'Not specified',
                        'location': locations,
                        'posting_date': posted_date,
                        'remote': remote,
                        'region': 'Not specified',  # Workday doesn't always provide region
                        'url': job_url
                    }

                    jobs.append(job_info)
                    total_fetched += 1

                except Exception as e:
                    self.log(f"Error parsing job: {e}", "WARNING")
                    continue

            # Check if there are more pages
            total_jobs = data.get('total', 0)
            self.log(f"Fetched {total_fetched}/{total_jobs} jobs")

            if total_fetched >= total_jobs:
                break

            offset += limit

        self.log(f"Completed: {len(jobs)} jobs scraped")
        return jobs
