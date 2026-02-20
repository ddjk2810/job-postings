"""
UKG/UltiPro Platform Scraper

Scrapes job postings from UKG (Ultimate Kronos Group) UltiPro job boards.
UltiPro embeds job data as JSON in the page or renders it via JavaScript.
"""

import json
import re
from bs4 import BeautifulSoup
from scrapers.base_scraper import BaseScraper


class UltiProScraper(BaseScraper):
    """Scraper for UKG/UltiPro-based career sites."""

    def scrape(self):
        """
        Scrape jobs from UltiPro career site.

        Returns:
            list: List of job dictionaries
        """
        self.log("Starting UltiPro scrape...")

        response = self.make_request(self.url)
        if not response:
            self.log("Failed to fetch UltiPro page", "ERROR")
            return []

        html = response.text

        # Try extracting embedded JSON data first
        jobs = self._extract_json_data(html)
        if jobs:
            return jobs

        # Try the UltiPro API endpoint
        jobs = self._try_api(html)
        if jobs:
            return jobs

        # Fallback to HTML parsing
        self.log("Trying HTML parsing fallback...")
        return self._parse_html(html)

    def _extract_json_data(self, html):
        """Try to extract job data from embedded JSON in script tags."""
        # UltiPro often embeds job data in script tags
        patterns = [
            r'var\s+opportunities\s*=\s*(\[.*?\]);',
            r'var\s+jobPostings\s*=\s*(\[.*?\]);',
            r'"opportunities"\s*:\s*(\[.*?\])',
            r'"jobPostings"\s*:\s*(\[.*?\])',
            r'window\.__INITIAL_STATE__\s*=\s*({.*?});',
        ]

        for pattern in patterns:
            match = re.search(pattern, html, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(1))
                    if isinstance(data, dict):
                        # Extract jobs from nested structure
                        data = data.get('opportunities', data.get('jobPostings', []))
                    if isinstance(data, list) and data:
                        return self._parse_json_jobs(data)
                except (json.JSONDecodeError, ValueError):
                    continue
        return None

    def _try_api(self, html):
        """Try the UltiPro REST API if we can find the board key."""
        # Extract board key from URL or page
        # URL format: https://recruiting{N}.ultipro.com/{COMPANY}/JobBoard/{BOARD_KEY}/
        match = re.search(r'JobBoard/([a-f0-9-]+)', self.url, re.IGNORECASE)
        if not match:
            match = re.search(r'JobBoard/([a-f0-9-]+)', html, re.IGNORECASE)
        if not match:
            return None

        board_key = match.group(1)

        # Also extract company key from URL
        company_match = re.search(r'ultipro\.com/([^/]+)/JobBoard', self.url, re.IGNORECASE)
        if not company_match:
            return None

        company_key = company_match.group(1)

        # Extract the host from the configured URL (handles recruiting, recruiting2, etc.)
        from urllib.parse import urlparse
        parsed = urlparse(self.url)
        host = f"{parsed.scheme}://{parsed.netloc}"

        # UltiPro API endpoint
        api_url = f"{host}/{company_key}/JobBoard/{board_key}/JobBoardView/LoadSearchResults"

        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }

        payload = {
            'opportunitySearch': {
                'Top': 200,
                'Skip': 0,
                'QueryString': '',
                'OrderBy': [{'Value': 'postedDateDesc', 'PropertyName': 'PostedDate', 'Ascending': False}]
            }
        }

        response = self.make_request(api_url, method='POST', json=payload, headers=headers)
        if not response:
            return None

        try:
            data = response.json()
        except (json.JSONDecodeError, ValueError):
            return None

        opportunities = data.get('opportunities', [])
        if not opportunities:
            return None

        return self._parse_json_jobs(opportunities)

    def _parse_location(self, item):
        """Extract a clean location string from UltiPro job data."""
        # Try flat fields first (some UltiPro instances use these)
        city = item.get('City', item.get('city', ''))
        state = item.get('State', item.get('state', ''))
        country = item.get('Country', item.get('country', ''))
        if isinstance(city, str) and city:
            parts = [p for p in [city, state, country] if isinstance(p, str) and p]
            if parts:
                return ', '.join(parts)

        # Parse nested Locations array (recruiting2.ultipro.com format)
        locations = item.get('Locations', item.get('locations', []))
        if isinstance(locations, list) and locations:
            loc = locations[0]  # Use first location
            if isinstance(loc, dict):
                # Try LocalizedName first (e.g. "Remote - Kansas City")
                name = loc.get('LocalizedName', '')
                if name:
                    return name

                # Fall back to Address fields
                addr = loc.get('Address', {})
                if isinstance(addr, dict):
                    parts = []
                    addr_city = addr.get('City', '')
                    addr_state = addr.get('State', {})
                    addr_country = addr.get('Country', {})
                    if addr_city:
                        parts.append(addr_city)
                    if isinstance(addr_state, dict) and addr_state.get('Name'):
                        parts.append(addr_state['Name'])
                    elif isinstance(addr_state, str) and addr_state:
                        parts.append(addr_state)
                    if isinstance(addr_country, dict) and addr_country.get('Name'):
                        parts.append(addr_country['Name'])
                    elif isinstance(addr_country, str) and addr_country:
                        parts.append(addr_country)
                    if parts:
                        return ', '.join(parts)

        return item.get('location', 'Not specified')

    def _parse_json_jobs(self, job_list):
        """Parse job data from JSON array."""
        jobs = []

        # Extract the base URL for building job detail links
        # Strip query params from the board URL
        from urllib.parse import urlparse, urljoin
        parsed = urlparse(self.url)
        # Board path is like: /{COMPANY}/JobBoard/{BOARD_KEY}/
        board_path = parsed.path.rstrip('/')
        base_url = f"{parsed.scheme}://{parsed.netloc}{board_path}"

        for item in job_list:
            try:
                title = item.get('Title', item.get('title', item.get('name', '')))
                if not title:
                    continue

                location = self._parse_location(item)

                department = (item.get('Department') or item.get('department') or
                             item.get('FunctionalArea') or item.get('JobCategory') or
                             'Not specified')
                posting_date = item.get('PostedDate', item.get('postedDate', 'Not specified'))

                # Build URL
                job_id = item.get('Id', item.get('id', item.get('RequisitionNumber', '')))
                job_url = ''
                if job_id:
                    job_url = f"{base_url}/OpportunityDetail?opportunityId={job_id}"

                remote = 'Yes' if 'remote' in str(location).lower() or 'remote' in str(title).lower() else 'No'

                jobs.append({
                    'title': str(title),
                    'department': str(department) if department else 'Not specified',
                    'location': str(location) if location else 'Not specified',
                    'posting_date': str(posting_date) if posting_date else 'Not specified',
                    'remote': remote,
                    'region': 'Not specified',
                    'url': job_url
                })
            except Exception as e:
                self.log(f"Error parsing job: {e}", "WARNING")
                continue

        self.log(f"Completed (JSON): {len(jobs)} jobs scraped")
        return jobs

    def _parse_html(self, html):
        """Fallback: parse HTML for job listings."""
        soup = BeautifulSoup(html, 'html.parser')
        jobs = []

        # UltiPro uses various selectors for job cards
        job_elements = (
            soup.select('.opportunity-node') or
            soup.select('[class*="job-item"]') or
            soup.select('[class*="opportunity"]') or
            soup.select('a[href*="OpportunityDetail"]')
        )

        for el in job_elements:
            try:
                # Get title
                title_el = el.select_one('h3, h4, [class*="title"]')
                if title_el:
                    title = title_el.get_text(strip=True)
                elif el.name == 'a':
                    title = el.get_text(strip=True)
                else:
                    continue

                if not title:
                    continue

                # Get URL
                if el.name == 'a':
                    job_url = el.get('href', '')
                else:
                    link = el.select_one('a[href*="OpportunityDetail"]')
                    job_url = link.get('href', '') if link else ''

                if job_url and not job_url.startswith('http'):
                    base = self.url.split('/JobBoard')[0] if '/JobBoard' in self.url else self.url
                    job_url = base + job_url

                # Get location
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
