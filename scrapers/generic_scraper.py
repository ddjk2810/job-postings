"""
Generic Scraper

Attempts to scrape job postings from various career sites using common patterns.
This is a fallback scraper for sites without custom implementations.
"""

import re
import json
from scrapers.base_scraper import BaseScraper


class GenericScraper(BaseScraper):
    """Generic scraper for career sites."""

    def scrape(self):
        """
        Attempt to scrape jobs using common patterns.

        Returns:
            list: List of job dictionaries (may be empty if unsuccessful)
        """
        self.log("Starting generic scrape...")
        self.log("Note: Generic scraper has limited capabilities", "WARNING")

        response = self.make_request(self.url)

        if not response:
            self.log("Failed to fetch page", "ERROR")
            return []

        jobs = []

        # Try different patterns
        jobs = (
            self._try_json_ld(response.text) or
            self._try_greenhouse(response.text) or
            self._try_lever(response.text) or
            self._try_json_data(response.text) or
            []
        )

        if jobs:
            self.log(f"Completed: {len(jobs)} jobs scraped")
        else:
            self.log("Could not extract jobs - site may require custom scraper", "WARNING")
            self.log("Possible reasons:", "WARNING")
            self.log("  - Jobs loaded via JavaScript (not in initial HTML)", "WARNING")
            self.log("  - Uses third-party platform (RippleMatch, etc.)", "WARNING")
            self.log("  - Requires authentication or special headers", "WARNING")

        return jobs

    def _try_json_ld(self, html):
        """Try to extract jobs from JSON-LD structured data."""
        self.log("Trying JSON-LD extraction...")

        pattern = r'<script type="application/ld\+json">(.*?)</script>'
        matches = re.findall(pattern, html, re.DOTALL)

        jobs = []
        for match in matches:
            try:
                data = json.loads(match)

                # Check if it's a JobPosting
                if isinstance(data, dict) and data.get('@type') == 'JobPosting':
                    job = self._parse_json_ld_job(data)
                    if job:
                        jobs.append(job)

                # Check if it's a list containing JobPostings
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and item.get('@type') == 'JobPosting':
                            job = self._parse_json_ld_job(item)
                            if job:
                                jobs.append(job)

            except json.JSONDecodeError:
                continue

        if jobs:
            self.log(f"Found {len(jobs)} jobs via JSON-LD")
        return jobs if jobs else None

    def _parse_json_ld_job(self, data):
        """Parse a JobPosting from JSON-LD."""
        try:
            location = data.get('jobLocation', {})
            if isinstance(location, dict):
                address = location.get('address', {})
                if isinstance(address, dict):
                    city = address.get('addressLocality', '')
                    country = address.get('addressCountry', '')
                    location_str = f"{city}, {country}".strip(', ') or 'Not specified'
                else:
                    location_str = 'Not specified'
            else:
                location_str = 'Not specified'

            return {
                'title': data.get('title', 'Not specified'),
                'department': data.get('department', 'Not specified'),
                'location': location_str,
                'posting_date': data.get('datePosted', 'Not specified'),
                'remote': 'Yes' if 'remote' in str(data).lower() else 'No',
                'region': 'Not specified',
                'url': data.get('url', '')
            }
        except Exception:
            return None

    def _try_greenhouse(self, html):
        """Try to extract jobs from Greenhouse ATS."""
        self.log("Trying Greenhouse extraction...")

        # Greenhouse often embeds data in a specific div or script tag
        # Pattern varies, but commonly has class "job" or data-department
        pattern = r'data-department="([^"]*)".*?data-title="([^"]*)".*?data-location="([^"]*)"'
        matches = re.findall(pattern, html, re.DOTALL)

        if matches:
            jobs = []
            for dept, title, location in matches:
                jobs.append({
                    'title': title,
                    'department': dept,
                    'location': location,
                    'posting_date': 'Not specified',
                    'remote': 'Yes' if 'remote' in location.lower() else 'No',
                    'region': 'Not specified',
                    'url': ''
                })
            self.log(f"Found {len(jobs)} jobs via Greenhouse pattern")
            return jobs

        return None

    def _try_lever(self, html):
        """Try to extract jobs from Lever ATS."""
        self.log("Trying Lever extraction...")

        # Lever often uses a specific JSON structure
        pattern = r'window\.LEVER_JOBS\s*=\s*(\[.*?\]);'
        match = re.search(pattern, html, re.DOTALL)

        if match:
            try:
                jobs_data = json.loads(match.group(1))
                jobs = []

                for job in jobs_data:
                    jobs.append({
                        'title': job.get('text', 'Not specified'),
                        'department': job.get('categories', {}).get('team', 'Not specified'),
                        'location': job.get('categories', {}).get('location', 'Not specified'),
                        'posting_date': job.get('createdAt', 'Not specified'),
                        'remote': 'Yes' if job.get('categories', {}).get('commitment') == 'Remote' else 'No',
                        'region': 'Not specified',
                        'url': job.get('hostedUrl', '')
                    })

                self.log(f"Found {len(jobs)} jobs via Lever")
                return jobs

            except json.JSONDecodeError:
                pass

        return None

    def _try_json_data(self, html):
        """Try to find any JSON data containing job listings."""
        self.log("Trying generic JSON extraction...")

        # Look for common variable names
        patterns = [
            r'var jobs\s*=\s*(\[.*?\]);',
            r'let jobs\s*=\s*(\[.*?\]);',
            r'const jobs\s*=\s*(\[.*?\]);',
            r'window\.jobs\s*=\s*(\[.*?\]);',
            r'"jobs"\s*:\s*(\[.*?\])',
        ]

        for pattern in patterns:
            match = re.search(pattern, html, re.DOTALL | re.IGNORECASE)
            if match:
                try:
                    jobs_data = json.loads(match.group(1))
                    if isinstance(jobs_data, list) and len(jobs_data) > 0:
                        # Try to parse if it looks like job data
                        if isinstance(jobs_data[0], dict):
                            jobs = self._parse_generic_json(jobs_data)
                            if jobs:
                                self.log(f"Found {len(jobs)} jobs via generic JSON")
                                return jobs
                except (json.JSONDecodeError, IndexError):
                    continue

        return None

    def _parse_generic_json(self, jobs_data):
        """Try to parse generic JSON job data."""
        jobs = []

        for job in jobs_data:
            if not isinstance(job, dict):
                continue

            # Try to find title (most critical field)
            title = (
                job.get('title') or
                job.get('job_title') or
                job.get('name') or
                job.get('position') or
                'Not specified'
            )

            if title == 'Not specified':
                continue  # Skip if we can't find a title

            # Try to find other fields with common names
            department = (
                job.get('department') or
                job.get('team') or
                job.get('category') or
                'Not specified'
            )

            location = (
                job.get('location') or
                job.get('city') or
                job.get('office') or
                'Not specified'
            )

            jobs.append({
                'title': title,
                'department': department,
                'location': location,
                'posting_date': job.get('posted_date') or job.get('created_at') or 'Not specified',
                'remote': 'Yes' if job.get('remote') or 'remote' in str(location).lower() else 'No',
                'region': job.get('region') or 'Not specified',
                'url': job.get('url') or job.get('link') or ''
            })

        return jobs if jobs else None
