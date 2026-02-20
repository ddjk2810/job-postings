"""
Teamtailor Platform Scraper

Scrapes job postings from Teamtailor-based career sites.
Tries the JSON endpoint first, falls back to HTML parsing.
"""

import json
from bs4 import BeautifulSoup
from scrapers.base_scraper import BaseScraper


class TeamtailorScraper(BaseScraper):
    """Scraper for Teamtailor-based career sites."""

    def scrape(self):
        """
        Scrape jobs from Teamtailor career site.

        Returns:
            list: List of job dictionaries
        """
        self.log("Starting Teamtailor scrape...")

        teamtailor_base = self.config.get('teamtailor_base')
        if not teamtailor_base:
            self.log("No teamtailor_base configured", "ERROR")
            return []

        base_url = f"https://{teamtailor_base}"

        # Try JSON endpoint first
        jobs = self._try_json_endpoint(base_url)
        if jobs:
            return jobs

        # Fallback to HTML parsing
        self.log("JSON endpoint failed, trying HTML parsing...")
        return self._parse_html(base_url)

    def _try_json_endpoint(self, base_url):
        """Try fetching jobs from the Teamtailor JSON API."""
        api_url = f"{base_url}/jobs"

        headers = {
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = self.make_request(api_url, headers=headers)
        if not response:
            return None

        # Check if we got JSON back
        content_type = response.headers.get('Content-Type', '')
        if 'json' not in content_type:
            return None

        try:
            data = response.json()
        except (json.JSONDecodeError, ValueError):
            return None

        # Teamtailor JSON can be a list of jobs or nested under 'data'/'jobs'
        job_list = data if isinstance(data, list) else data.get('data', data.get('jobs', []))
        if not isinstance(job_list, list) or not job_list:
            return None

        jobs = []
        for item in job_list:
            try:
                attrs = item.get('attributes', item) if isinstance(item, dict) else {}

                title = attrs.get('title', item.get('title', ''))
                if not title:
                    continue

                location = attrs.get('location', item.get('location', 'Not specified')) or 'Not specified'
                department = attrs.get('department', item.get('department', 'Not specified')) or 'Not specified'

                # Build URL from links or ID
                links = item.get('links', {})
                job_url = links.get('careersite-job-url', '')
                if not job_url:
                    job_id = item.get('id', '')
                    job_url = f"{base_url}/jobs/{job_id}" if job_id else ''

                remote = 'Yes' if 'remote' in str(location).lower() else 'No'

                jobs.append({
                    'title': title,
                    'department': department,
                    'location': location,
                    'posting_date': attrs.get('created-at', 'Not specified'),
                    'remote': remote,
                    'region': 'Not specified',
                    'url': job_url
                })
            except Exception as e:
                self.log(f"Error parsing job: {e}", "WARNING")
                continue

        if jobs:
            self.log(f"Completed (JSON): {len(jobs)} jobs scraped")
        return jobs if jobs else None

    def _parse_html(self, base_url):
        """Fallback: parse HTML career page for job listings."""
        jobs_url = f"{base_url}/jobs"
        response = self.make_request(jobs_url)
        if not response:
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        jobs = []

        # Teamtailor typically uses <a> tags with /jobs/ in href for job cards
        job_links = soup.select('a[href*="/jobs/"]')

        seen_urls = set()
        for link in job_links:
            href = link.get('href', '')
            if not href or href in seen_urls:
                continue

            # Build full URL
            if href.startswith('/'):
                full_url = base_url + href
            elif not href.startswith('http'):
                full_url = base_url + '/' + href
            else:
                full_url = href

            # Skip non-job links (like /jobs or /jobs?department=...)
            path = href.rstrip('/')
            if path == '/jobs' or '?' in path:
                continue

            seen_urls.add(href)

            # Extract title from link text or child elements
            title = link.get_text(strip=True)
            if not title or len(title) < 3:
                continue

            # Try to find location from sibling/child elements
            location = 'Not specified'
            parent = link.parent
            if parent:
                # Look for location text in parent container
                loc_el = parent.select_one('[class*="location"], [class*="meta"]')
                if loc_el:
                    location = loc_el.get_text(strip=True)

            # Try to get department
            department = 'Not specified'
            dept_el = parent.select_one('[class*="department"], [class*="category"]') if parent else None
            if dept_el:
                department = dept_el.get_text(strip=True)

            remote = 'Yes' if 'remote' in str(location).lower() else 'No'

            jobs.append({
                'title': title,
                'department': department,
                'location': location,
                'posting_date': 'Not specified',
                'remote': remote,
                'region': 'Not specified',
                'url': full_url
            })

        self.log(f"Completed (HTML): {len(jobs)} jobs scraped")
        return jobs
