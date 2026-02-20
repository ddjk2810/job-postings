"""
Static HTML Scraper

Generic BeautifulSoup scraper for simple HTML career pages.
Looks for job headings and links within a configurable container.
"""

from bs4 import BeautifulSoup
from scrapers.base_scraper import BaseScraper


class StaticHTMLScraper(BaseScraper):
    """Generic scraper for simple static HTML career pages."""

    def scrape(self):
        """
        Scrape jobs from a static HTML career page.

        Returns:
            list: List of job dictionaries
        """
        self.log("Starting static HTML scrape...")

        response = self.make_request(self.url)
        if not response:
            self.log("Failed to fetch page", "ERROR")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')

        # Optionally scope to a specific container
        container_selector = self.config.get('jobs_container_selector')
        if container_selector:
            container = soup.select_one(container_selector)
            if not container:
                self.log(f"Container '{container_selector}' not found, searching full page", "WARNING")
                container = soup
        else:
            container = soup

        jobs = []

        # Strategy 1: Find job links (most common pattern)
        job_links = self._find_job_links(container)
        if job_links:
            jobs = job_links

        # Strategy 2: Find job headings if no links found
        if not jobs:
            jobs = self._find_job_headings(container)

        self.log(f"Completed: {len(jobs)} jobs scraped")
        return jobs

    def _find_job_links(self, container):
        """Find jobs from anchor tags that look like job postings."""
        jobs = []
        seen = set()

        # If a URL pattern is configured, only match links containing that pattern
        job_url_pattern = self.config.get('job_url_pattern')

        # Look for links that might be job postings
        links = container.find_all('a', href=True)

        for link in links:
            href = link.get('href', '')
            title = link.get_text(strip=True)

            # If URL pattern configured, only keep matching links
            if job_url_pattern and job_url_pattern not in href:
                continue

            # Skip navigation, empty, and very short titles
            if not title or len(title) < 5:
                continue

            # Skip common non-job links
            skip_patterns = ['mailto:', 'javascript:', '#', 'linkedin.com', 'twitter.com',
                             'facebook.com', 'login', 'sign-in', 'about', 'contact',
                             'privacy', 'terms', 'cookie']
            if any(p in href.lower() for p in skip_patterns):
                continue

            # Skip common CTA / navigation text
            skip_titles = ['find out more', 'read more', 'learn more', 'apply now',
                           'view details', 'see details', 'click here', 'view all']
            if title.lower().strip() in skip_titles:
                continue

            # Deduplicate
            key = title.lower().strip()
            if key in seen:
                continue
            seen.add(key)

            # Build full URL
            if href.startswith('/'):
                from urllib.parse import urlparse
                parsed = urlparse(self.url)
                full_url = f"{parsed.scheme}://{parsed.netloc}{href}"
            elif not href.startswith('http'):
                full_url = self.url.rstrip('/') + '/' + href
            else:
                full_url = href

            # Try to extract location from surrounding text
            location = 'Not specified'
            parent = link.parent
            if parent:
                siblings_text = parent.get_text(separator=' | ', strip=True)
                # Look for location patterns (City, State or Country)
                import re
                loc_match = re.search(r'(?:Location|Office|Based in)[:\s]+([^|]+)', siblings_text, re.IGNORECASE)
                if loc_match:
                    location = loc_match.group(1).strip()

            remote = 'Yes' if 'remote' in title.lower() or 'remote' in location.lower() else 'No'

            jobs.append({
                'title': title,
                'department': 'Not specified',
                'location': location,
                'posting_date': 'Not specified',
                'remote': remote,
                'region': 'Not specified',
                'url': full_url
            })

        return jobs

    def _find_job_headings(self, container):
        """Find jobs from heading elements (h2, h3, h4) that look like job titles."""
        jobs = []
        seen = set()

        for heading in container.find_all(['h2', 'h3', 'h4']):
            title = heading.get_text(strip=True)
            if not title or len(title) < 5:
                continue

            # Skip common section headings
            skip_titles = ['about', 'our team', 'benefits', 'perks', 'culture',
                           'why join', 'our values', 'open positions', 'careers',
                           'current openings', 'job openings']
            if title.lower().strip() in skip_titles:
                continue

            key = title.lower().strip()
            if key in seen:
                continue
            seen.add(key)

            # Try to find a link
            link = heading.find('a', href=True)
            if not link:
                # Check parent or next sibling
                parent = heading.parent
                if parent:
                    link = parent.find('a', href=True)

            job_url = ''
            if link:
                href = link.get('href', '')
                if href.startswith('/'):
                    from urllib.parse import urlparse
                    parsed = urlparse(self.url)
                    job_url = f"{parsed.scheme}://{parsed.netloc}{href}"
                elif href.startswith('http'):
                    job_url = href

            # Try to find location from adjacent elements
            location = 'Not specified'
            next_el = heading.find_next_sibling()
            if next_el:
                text = next_el.get_text(strip=True)
                if text and len(text) < 100:
                    location = text

            remote = 'Yes' if 'remote' in title.lower() or 'remote' in location.lower() else 'No'

            jobs.append({
                'title': title,
                'department': 'Not specified',
                'location': location,
                'posting_date': 'Not specified',
                'remote': remote,
                'region': 'Not specified',
                'url': job_url or self.url
            })

        return jobs
