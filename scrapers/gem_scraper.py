"""
Gem Platform Scraper

Scrapes job postings from Gem-based career sites.
Gem is a recruiting platform that requires JavaScript rendering.
"""

from selenium.webdriver.common.by import By
from scrapers.headless_scraper import HeadlessScraper
import time


class GemScraper(HeadlessScraper):
    """Scraper for Gem-based career sites."""

    def _scrape_jobs(self):
        """
        Scrape jobs from Gem job board.

        Returns:
            list: List of job dictionaries
        """
        self.log("Starting Gem scrape...")

        url = self.config.get('url')
        if not url:
            self.log("No URL configured", "ERROR")
            return []

        self.log(f"Loading page: {url}")
        self.driver.get(url)

        # Wait for page to load and jobs to render
        time.sleep(3)

        jobs = []

        try:
            # Try multiple selectors for job listings
            # Gem typically uses divs or links with job-related classes
            job_selectors = [
                'a[href*="/jobs/"]',
                '[data-testid*="job"]',
                '.job-card',
                '.job-listing',
                '.job-row',
                'a[href*="job"]',
                '[class*="JobCard"]',
                '[class*="job-card"]',
                '[class*="posting"]',
            ]

            job_elements = []
            for selector in job_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        self.log(f"Found {len(elements)} elements with selector: {selector}")
                        job_elements = elements
                        break
                except Exception:
                    continue

            if not job_elements:
                # Try finding all links and filter for job-related ones
                self.log("Trying to find job links...")
                all_links = self.driver.find_elements(By.TAG_NAME, 'a')
                job_elements = [
                    link for link in all_links
                    if '/jobs/' in (link.get_attribute('href') or '')
                    or 'job' in (link.get_attribute('class') or '').lower()
                ]
                self.log(f"Found {len(job_elements)} potential job links")

            # Extract job information
            seen_urls = set()
            for element in job_elements:
                try:
                    # Get job URL
                    job_url = element.get_attribute('href')
                    if not job_url or job_url in seen_urls:
                        continue
                    if '/jobs/' not in job_url:
                        continue

                    seen_urls.add(job_url)

                    # Try to get job title
                    title = None

                    # Try getting text from the element
                    title = element.text.strip()

                    # If element has nested structure, try to find title
                    if not title or len(title) > 200:
                        try:
                            title_el = element.find_element(By.CSS_SELECTOR, 'h2, h3, h4, [class*="title"], [class*="Title"]')
                            title = title_el.text.strip()
                        except Exception:
                            pass

                    if not title:
                        # Extract from URL as last resort
                        title = job_url.split('/')[-1].replace('-', ' ').title()

                    # Try to get location
                    location = 'Not specified'
                    try:
                        loc_el = element.find_element(By.CSS_SELECTOR, '[class*="location"], [class*="Location"]')
                        location = loc_el.text.strip()
                    except Exception:
                        pass

                    # Try to get department
                    department = 'Not specified'
                    try:
                        dept_el = element.find_element(By.CSS_SELECTOR, '[class*="department"], [class*="Department"], [class*="team"], [class*="Team"]')
                        department = dept_el.text.strip()
                    except Exception:
                        pass

                    # Check if remote
                    remote = 'No'
                    if 'remote' in location.lower() or 'remote' in title.lower():
                        remote = 'Yes'

                    job_info = {
                        'title': title[:200] if title else 'Not specified',
                        'department': department,
                        'location': location,
                        'posting_date': 'Not specified',
                        'remote': remote,
                        'region': 'Not specified',
                        'url': job_url
                    }

                    jobs.append(job_info)

                except Exception as e:
                    self.log(f"Error parsing job element: {e}", "WARNING")
                    continue

            # If still no jobs, try extracting from page source
            if not jobs:
                self.log("Attempting to extract jobs from page source...")
                page_source = self.driver.page_source

                # Look for JSON data embedded in the page
                import re
                import json

                # Try to find JSON with jobs data
                json_patterns = [
                    r'"jobs"\s*:\s*(\[.*?\])',
                    r'"positions"\s*:\s*(\[.*?\])',
                    r'"openings"\s*:\s*(\[.*?\])',
                ]

                for pattern in json_patterns:
                    matches = re.findall(pattern, page_source, re.DOTALL)
                    for match in matches:
                        try:
                            job_data = json.loads(match)
                            if isinstance(job_data, list) and job_data:
                                self.log(f"Found {len(job_data)} jobs in embedded JSON")
                                for job in job_data:
                                    job_info = {
                                        'title': job.get('title', job.get('name', 'Not specified')),
                                        'department': job.get('department', job.get('team', 'Not specified')),
                                        'location': job.get('location', 'Not specified'),
                                        'posting_date': job.get('posted_at', job.get('created_at', 'Not specified')),
                                        'remote': 'Yes' if job.get('remote') else 'No',
                                        'region': 'Not specified',
                                        'url': job.get('url', job.get('apply_url', url))
                                    }
                                    jobs.append(job_info)
                                break
                        except json.JSONDecodeError:
                            continue

        except Exception as e:
            self.log(f"Error scraping jobs: {e}", "ERROR")

        self.log(f"Completed: {len(jobs)} jobs scraped")
        return jobs
