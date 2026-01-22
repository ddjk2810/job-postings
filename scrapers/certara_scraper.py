"""
Certara Scraper

Scrapes job postings from Certara's careers page using headless browser.
Handles pagination and extracts location/department info.
"""

from selenium.webdriver.common.by import By
from scrapers.headless_scraper import HeadlessScraper
import time
import re


class CertaraScraper(HeadlessScraper):
    """Scraper for Certara careers site (Jibe/iCIMS platform)."""

    def _scrape_jobs(self):
        """
        Scrape jobs from Certara using headless browser.

        Returns:
            list: List of job dictionaries
        """
        self.log("Starting Certara scrape...")

        # Load the page
        self.driver.get(self.url)
        self.log(f"Loaded page: {self.url}")

        # Wait for page to load
        time.sleep(5)

        all_jobs = []
        page = 1
        max_pages = 10  # Safety limit

        while page <= max_pages:
            self.log(f"Scraping page {page}...")

            # Wait for job listings
            time.sleep(3)

            # Get jobs from current page
            page_jobs = self._extract_jobs_from_page()

            if not page_jobs:
                self.log("No jobs found on this page")
                break

            all_jobs.extend(page_jobs)
            self.log(f"Found {len(page_jobs)} jobs on page {page}")

            # Check if there is a next page
            if not self._go_to_next_page():
                break

            page += 1
            time.sleep(2)

        # Deduplicate by URL
        seen_urls = set()
        unique_jobs = []
        for job in all_jobs:
            if job['url'] not in seen_urls:
                seen_urls.add(job['url'])
                unique_jobs.append(job)

        self.log(f"Completed: {len(unique_jobs)} unique jobs scraped")
        return unique_jobs

    def _extract_jobs_from_page(self):
        """Extract jobs from the current page."""
        jobs = []

        # Get page text for parsing
        body_text = self.driver.find_element(By.TAG_NAME, 'body').text
        lines = body_text.split('\n')

        # Find all job links
        job_links = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="/jobs/"][href*="lang=en"]')

        seen_urls = set()

        for link in job_links:
            try:
                url = link.get_attribute('href')
                title = link.text.strip()

                # Skip invalid entries
                if not url or not title or len(title) < 3:
                    continue
                if 'login' in url.lower() or title.lower() in ['apply now', 'apply', 'read more']:
                    continue
                if url in seen_urls:
                    continue

                seen_urls.add(url)

                # Extract job ID from URL
                job_id_match = re.search(r'/jobs/(\d+)', url)
                job_id = job_id_match.group(1) if job_id_match else None

                # Find location and other info by searching body text
                location = 'Not specified'
                department = 'Not specified'
                remote = 'No'

                if job_id:
                    # Look for this specific job in the body text
                    for i, line in enumerate(lines):
                        if f'Req ID: {job_id}' in line or f'Req ID:{job_id}' in line:
                            # Look backwards and forwards for location
                            context_start = max(0, i - 5)
                            context_end = min(len(lines), i + 10)
                            context = lines[context_start:context_end]

                            for j, ctx_line in enumerate(context):
                                if ctx_line.strip() == 'Location':
                                    # Next non-empty lines are location
                                    loc_parts = []
                                    for k in range(j + 1, min(j + 4, len(context))):
                                        part = context[k].strip()
                                        if part and part not in ['home', 'Remote', 'Apply Now', 'Category']:
                                            loc_parts.append(part)
                                        elif part in ['home', 'Remote', 'Apply Now', 'Category']:
                                            break
                                    if loc_parts:
                                        location = ', '.join(loc_parts)

                                if ctx_line.strip() == 'Remote':
                                    remote = 'Yes'

                                if ctx_line.strip() == 'Category':
                                    if j + 1 < len(context):
                                        dept = context[j + 1].strip()
                                        if dept and dept not in ['Apply Now', 'home', 'Remote']:
                                            department = dept
                            break

                # Also check title for remote
                if 'remote' in title.lower() or 'remote' in location.lower():
                    remote = 'Yes'

                jobs.append({
                    'title': title,
                    'department': department,
                    'location': location,
                    'posting_date': 'Not specified',
                    'remote': remote,
                    'region': 'Not specified',
                    'url': url
                })

            except Exception as e:
                self.log(f"Error parsing job: {e}", "WARNING")
                continue

        return jobs

    def _go_to_next_page(self):
        """Navigate to next page. Returns True if successful."""
        try:
            # Look for next page button/link
            next_selectors = [
                'button[aria-label*="next" i]',
                'a[aria-label*="next" i]',
                'button[class*="next"]',
                'a[class*="next"]',
                'li.next a',
                'a.next'
            ]

            for sel in next_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, sel)
                    for elem in elements:
                        if elem.is_displayed() and elem.is_enabled():
                            # Check if not disabled
                            classes = elem.get_attribute('class') or ''
                            parent_classes = ''
                            try:
                                parent = elem.find_element(By.XPATH, './..')
                                parent_classes = parent.get_attribute('class') or ''
                            except:
                                pass

                            if 'disabled' not in classes.lower() and 'disabled' not in parent_classes.lower():
                                elem.click()
                                time.sleep(3)
                                return True
                except:
                    continue

            return False
        except Exception as e:
            self.log(f"Could not navigate to next page: {e}", "DEBUG")
            return False
