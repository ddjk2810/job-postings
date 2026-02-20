"""
Oracle Fusion HCM Scraper

Scrapes job postings from Oracle Fusion HCM (Cloud) career sites.
Uses the REST API endpoint for recruiting job requisitions.
"""

import json
import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from scrapers.base_scraper import BaseScraper


class OracleHCMScraper(BaseScraper):
    """Scraper for Oracle Fusion HCM career sites."""

    def scrape(self):
        """
        Scrape jobs from Oracle HCM career site.

        Returns:
            list: List of job dictionaries
        """
        self.log("Starting Oracle HCM scrape...")

        parsed = urlparse(self.url)
        host = f"{parsed.scheme}://{parsed.netloc}"

        # Try REST API first
        jobs = self._try_rest_api(host)
        if jobs:
            return jobs

        # Fallback to HTML parsing
        self.log("REST API failed, trying HTML parsing...")
        return self._parse_html(host)

    def _extract_site_code(self):
        """Extract the site code from the career page URL path."""
        # URL pattern: .../sites/{SITE_CODE}/jobs
        match = re.search(r'/sites/([^/]+)', self.url)
        return match.group(1) if match else 'CX'

    def _try_rest_api(self, host):
        """Try the Oracle HCM REST API for job requisitions."""
        api_url = f"{host}/hcmRestApi/resources/latest/recruitingCEJobRequisitions"
        site_code = self._extract_site_code()

        headers = {
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }

        all_jobs = []
        offset = 0
        page_size = 25
        total_jobs = None

        while True:
            # Oracle HCM uses finder params with semicolons and commas
            # Pagination offset goes inside the finder param
            finder = f"findReqs;siteNumber={site_code}"
            if offset > 0:
                finder += f",offset={offset}"

            params = {
                'onlyData': 'true',
                'expand': 'requisitionList',
                'finder': finder,
                'limit': page_size,
                'offset': 0
            }

            response = self.make_request(api_url, headers=headers, params=params)
            if not response:
                break

            try:
                data = response.json()
            except (json.JSONDecodeError, ValueError):
                break

            items = data.get('items', [])
            if not items:
                break

            # Jobs are nested: items[0].requisitionList
            for item in items:
                if total_jobs is None:
                    total_jobs = item.get('TotalJobsCount', 0)
                    self.log(f"Total jobs reported by API: {total_jobs}")

                req_list = item.get('requisitionList', [])
                if not isinstance(req_list, list):
                    continue

                for r in req_list:
                    job = self._parse_api_job(r, host, site_code)
                    if job:
                        all_jobs.append(job)

            # Check if we have all jobs
            if total_jobs and len(all_jobs) >= total_jobs:
                break

            offset += page_size

            # Safety limit
            if offset > 500:
                break

        if all_jobs:
            self.log(f"Completed (API): {len(all_jobs)} jobs scraped")
        return all_jobs if all_jobs else None

    def _parse_api_job(self, item, host, site_code='CX'):
        """Parse a single job from the API response."""
        title = item.get('Title', item.get('title', ''))
        if not title:
            return None

        # Location
        location = item.get('PrimaryLocation', item.get('primaryLocation', 'Not specified'))

        # Department / category (may be null for some instances)
        department = (item.get('Category') or item.get('category') or
                     item.get('Organization') or item.get('organization') or
                     item.get('JobFamily') or 'Not specified')

        # Posting date
        posting_date = item.get('PostedDate', item.get('postedDate', 'Not specified'))

        # URL
        req_id = item.get('Id', item.get('id', item.get('RequisitionNumber', '')))
        job_url = f"{host}/hcmUI/CandidateExperience/en/sites/{site_code}/job/{req_id}" if req_id else ''

        remote = 'Yes' if 'remote' in str(location).lower() else 'No'

        return {
            'title': str(title),
            'department': str(department) if department else 'Not specified',
            'location': str(location) if location else 'Not specified',
            'posting_date': str(posting_date) if posting_date else 'Not specified',
            'remote': remote,
            'region': 'Not specified',
            'url': job_url
        }

    def _parse_html(self, host):
        """Fallback: parse the candidate experience HTML page."""
        response = self.make_request(self.url)
        if not response:
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        jobs = []

        # Oracle HCM renders job cards with various structures
        job_elements = (
            soup.select('[class*="job-card"]') or
            soup.select('[class*="requisition"]') or
            soup.select('a[href*="/job/"]')
        )

        for el in job_elements:
            try:
                title_el = el.select_one('h2, h3, [class*="title"]')
                if title_el:
                    title = title_el.get_text(strip=True)
                elif el.name == 'a':
                    title = el.get_text(strip=True)
                else:
                    continue

                if not title:
                    continue

                # URL
                if el.name == 'a':
                    job_url = el.get('href', '')
                else:
                    link = el.select_one('a[href*="/job/"]')
                    job_url = link.get('href', '') if link else ''

                if job_url and not job_url.startswith('http'):
                    job_url = host + job_url

                # Location
                loc_el = el.select_one('[class*="location"]')
                location = loc_el.get_text(strip=True) if loc_el else 'Not specified'

                remote = 'Yes' if 'remote' in location.lower() else 'No'

                jobs.append({
                    'title': title,
                    'department': 'Not specified',
                    'location': location,
                    'posting_date': 'Not specified',
                    'remote': remote,
                    'region': 'Not specified',
                    'url': job_url
                })
            except Exception as e:
                self.log(f"Error parsing HTML job: {e}", "WARNING")
                continue

        self.log(f"Completed (HTML): {len(jobs)} jobs scraped")
        return jobs
