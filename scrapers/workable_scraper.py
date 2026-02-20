"""
Workable Platform Scraper

Scrapes job postings from Workable-based career sites via the public widget API.
"""

import json
from scrapers.base_scraper import BaseScraper


class WorkableScraper(BaseScraper):
    """Scraper for Workable-based career sites."""

    def scrape(self):
        """
        Scrape jobs from Workable public widget API.

        Returns:
            list: List of job dictionaries
        """
        self.log("Starting Workable scrape...")

        workable_id = self.config.get('workable_id')
        if not workable_id:
            self.log("No workable_id configured", "ERROR")
            return []

        api_url = f"https://apply.workable.com/api/v1/widget/accounts/{workable_id}"

        self.log(f"Fetching from Workable API: {api_url}")

        response = self.make_request(api_url)
        if not response:
            self.log("Failed to fetch from Workable API", "ERROR")
            return []

        try:
            data = response.json()
        except json.JSONDecodeError as e:
            self.log(f"Failed to parse JSON response: {e}", "ERROR")
            return []

        job_list = data.get('jobs', [])
        if not job_list:
            self.log("No jobs found in response", "WARNING")
            return []

        jobs = []
        for job in job_list:
            try:
                title = job.get('title', 'Not specified')
                if not title:
                    continue

                location = job.get('location', {})
                if isinstance(location, dict):
                    loc_parts = []
                    city = location.get('city', '')
                    region = location.get('region', '')
                    country = location.get('country', '')
                    if city:
                        loc_parts.append(city)
                    if region:
                        loc_parts.append(region)
                    if country:
                        loc_parts.append(country)
                    location_str = ', '.join(loc_parts) if loc_parts else 'Not specified'
                else:
                    location_str = str(location) if location else 'Not specified'

                department = job.get('department', 'Not specified') or 'Not specified'

                # Build URL
                shortcode = job.get('shortcode', '')
                job_url = f"https://apply.workable.com/{workable_id}/j/{shortcode}/" if shortcode else ''

                remote = 'Yes' if job.get('telecommute', False) or 'remote' in location_str.lower() else 'No'

                jobs.append({
                    'title': title,
                    'department': department,
                    'location': location_str,
                    'posting_date': job.get('published_on', 'Not specified'),
                    'remote': remote,
                    'region': 'Not specified',
                    'url': job_url
                })
            except Exception as e:
                self.log(f"Error parsing job: {e}", "WARNING")
                continue

        self.log(f"Completed: {len(jobs)} jobs scraped")
        return jobs
