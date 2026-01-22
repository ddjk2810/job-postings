"""
SuccessFactors (SAP) Scraper

Scrapes job postings from SAP SuccessFactors career portals.
Used by companies like Descartes.
"""

import re
from scrapers.base_scraper import BaseScraper


class SuccessFactorsScraper(BaseScraper):
    """Scraper for SAP SuccessFactors career sites."""

    def scrape(self):
        """
        Scrape jobs from SuccessFactors portal.

        Returns:
            list: List of job dictionaries
        """
        self.log("Starting SuccessFactors scrape...")

        # Get the all jobs page URL from config or construct it
        all_jobs_url = self.config.get('all_jobs_url', self.url)

        # For Descartes, the all jobs page is at a specific path
        if 'descartes' in self.slug.lower():
            all_jobs_url = 'https://jobs.descartes.com/go/View-All-Jobs/2574817/'

        response = self.make_request(all_jobs_url)
        if not response:
            self.log("Failed to fetch jobs page", "ERROR")
            return []

        html = response.text
        jobs = self._parse_jobs(html)

        self.log(f"Found {len(jobs)} jobs")
        return jobs

    def _parse_jobs(self, html):
        """
        Parse jobs from SuccessFactors HTML.

        Args:
            html (str): HTML content of jobs page

        Returns:
            list: List of job dictionaries
        """
        jobs = []
        seen_ids = set()

        # SuccessFactors tile-search layout pattern
        # Pattern: job link followed by location info in subsequent div
        # Matches: /job/[title-slug]/[id]/ with title text, then location
        job_pattern = r'<a[^>]*href="(/job/[^/]+/(\d+)/?)"[^>]*>([^<]+)</a>.*?</div>.*?<div[^>]*>([^<]*(?:US|CA|UK|DE|NL|AU|IN|PH|BR|UY|SE|SK|BG|Makati|Waterloo|Montevideo|Gurugram|Leipzig|Amersfoort|Zilina|City)[^<]*)</div>'

        matches = re.findall(job_pattern, html, re.DOTALL | re.IGNORECASE)

        for match in matches:
            job_path, job_id, title, location = match

            # Skip duplicates
            if job_id in seen_ids:
                continue
            seen_ids.add(job_id)

            # Clean title
            title = title.strip()
            if not title or len(title) < 3:
                continue

            # Skip navigation/footer links
            if any(skip in title.lower() for skip in ['search', 'alert', 'apply', 'sign in', 'register']):
                continue

            # Clean location
            location = location.strip()
            if not location:
                location = 'Not specified'

            # Construct full URL
            base_url = 'https://jobs.descartes.com' if 'descartes' in self.slug.lower() else self.url.rstrip('/')
            job_url = f"{base_url}{job_path}"

            # Determine if remote
            is_remote = 'remote' in title.lower() or 'remote' in location.lower()

            job_info = {
                'title': title,
                'department': 'Not specified',
                'location': location,
                'posting_date': 'Not specified',
                'remote': 'Yes' if is_remote else 'No',
                'region': self._extract_region(location),
                'url': job_url
            }
            jobs.append(job_info)

        # Fallback: if tile pattern didn't work, try simple link pattern
        if not jobs:
            simple_pattern = r'<a[^>]*href="(/job/[^"]+/(\d+)/)"[^>]*>([^<]+)</a>'
            matches = re.findall(simple_pattern, html, re.IGNORECASE)

            for match in matches:
                job_path, job_id, title = match

                if job_id in seen_ids:
                    continue
                seen_ids.add(job_id)

                title = title.strip()
                if not title or len(title) < 3:
                    continue

                if any(skip in title.lower() for skip in ['search', 'alert', 'apply', 'sign in', 'register']):
                    continue

                base_url = 'https://jobs.descartes.com' if 'descartes' in self.slug.lower() else self.url.rstrip('/')
                job_url = f"{base_url}{job_path}"

                job_info = {
                    'title': title,
                    'department': 'Not specified',
                    'location': 'Not specified',
                    'posting_date': 'Not specified',
                    'remote': 'No',
                    'region': 'Not specified',
                    'url': job_url
                }
                jobs.append(job_info)

        return jobs

    def _extract_region(self, location):
        """Extract region from location string."""
        location_lower = location.lower()

        # Country codes and names mapping
        regions = {
            'americas': ['us', 'usa', 'united states', 'canada', 'ca', 'brazil', 'br', 'mexico', 'mx', 'uruguay', 'uy', 'montevideo'],
            'emea': ['uk', 'gb', 'germany', 'de', 'france', 'fr', 'netherlands', 'nl', 'spain', 'es', 'italy', 'it',
                     'sweden', 'se', 'poland', 'pl', 'india', 'in', 'slovakia', 'sk', 'bulgaria', 'bg', 'malmo', 'woerden', 'leipzig', 'amersfoort', 'zilina', 'gurugram'],
            'apac': ['australia', 'au', 'singapore', 'sg', 'japan', 'jp', 'china', 'cn', 'philippines', 'ph', 'malaysia', 'my', 'makati']
        }

        for region, keywords in regions.items():
            for keyword in keywords:
                if keyword in location_lower:
                    return region.upper()

        return 'Not specified'
