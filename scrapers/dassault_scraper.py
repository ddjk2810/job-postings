"""
Dassault Systemes (3DS) Scraper

Scrapes job postings from Dassault Systemes careers page.
Uses Vue.js and loads jobs dynamically.
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from scrapers.headless_scraper import HeadlessScraper
import time
import re
import json


class DassaultScraper(HeadlessScraper):
    """Scraper for Dassault Systemes (3DS) careers site."""

    def _scrape_jobs(self):
        """
        Scrape jobs from Dassault Systemes using headless browser.

        Returns:
            list: List of job dictionaries
        """
        self.log("Starting Dassault Systemes scrape...")

        all_jobs = []
        seen_urls = set()

        # Load careers page
        base_url = "https://www.3ds.com/careers/jobs"
        self.driver.get(base_url)
        self.log(f"Loading: {base_url}")
        time.sleep(5)  # Wait for Vue.js to render

        # Wait for job cards to load
        try:
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[class*="job"], [class*="card"], a[href*="/careers/jobs/"]'))
            )
        except:
            self.log("Timeout waiting for job cards", "WARNING")

        # Scroll to load more content (infinite scroll handling)
        self._load_all_jobs()

        # Look for job-card-text elements (Dassault's specific structure)
        job_card_texts = self.driver.find_elements(By.CSS_SELECTOR, 'div.job-card-text')
        self.log(f"Found {len(job_card_texts)} job-card-text elements")

        if job_card_texts:
            for elem in job_card_texts:
                job = self._parse_job_card_text(elem, seen_urls)
                if job:
                    all_jobs.append(job)

        # If job-card-text didn't work, try other selectors
        if not all_jobs:
            job_selectors = [
                'a[href*="/careers/jobs/"]',
                '.ds-card',
                'article[class*="job"]',
                '.job-listing',
                'li[class*="job"]',
            ]

            for selector in job_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    self.log(f"Trying selector '{selector}': found {len(elements)} elements")

                    if len(elements) > 5:  # Likely found job listings
                        for elem in elements:
                            job = self._parse_job_element(elem, seen_urls)
                            if job:
                                all_jobs.append(job)
                        break

                except Exception as e:
                    self.log(f"Selector {selector} failed: {e}", "WARNING")
                    continue

        # If selectors don't work, try parsing from page source
        if len(all_jobs) == 0:
            self.log("Trying alternative parsing methods...")
            all_jobs = self._parse_from_source()

        self.log(f"Completed: {len(all_jobs)} total jobs scraped")
        return all_jobs

    def _load_all_jobs(self):
        """Load all jobs by scrolling or clicking 'load more'."""
        try:
            # Look for and click "Load More" or "Show More" button
            load_more_selectors = [
                'button[class*="load-more"]',
                'button[class*="show-more"]',
                'a[class*="load-more"]',
                'button:contains("More")',
                '[data-action="load-more"]',
            ]

            for _ in range(5):  # Try up to 5 times
                clicked = False
                for selector in load_more_selectors:
                    try:
                        button = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if button.is_displayed():
                            button.click()
                            time.sleep(2)
                            clicked = True
                            break
                    except:
                        continue

                if not clicked:
                    # Try scrolling instead
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)

                # Check if we reached the end
                try:
                    no_more = self.driver.find_element(By.CSS_SELECTOR, '[class*="no-more"], [class*="end-of-list"]')
                    if no_more.is_displayed():
                        break
                except:
                    pass

        except Exception as e:
            self.log(f"Load more failed: {e}", "WARNING")

    def _parse_job_card_text(self, elem, seen_urls):
        """Parse a job-card-text element (Dassault's specific format)."""
        try:
            text = elem.text.strip()
            if not text:
                return None

            lines = text.split('\n')
            if len(lines) < 2:
                return None

            # Structure is: Department, Title, Location, Type
            # Sometimes: Department, Title, Location (without type)
            department = lines[0].strip() if len(lines) > 0 else 'Not specified'
            title = lines[1].strip() if len(lines) > 1 else ''
            location = lines[2].strip() if len(lines) > 2 else 'Not specified'

            if not title or len(title) < 3:
                return None

            # Skip navigation items
            if any(skip in title.lower() for skip in ['search', 'filter', 'apply', 'menu', 'login']):
                return None

            # Skip if already seen (by title since we might not have URLs)
            title_key = title.lower()
            if title_key in seen_urls:
                return None
            seen_urls.add(title_key)

            # Try to find URL from parent element
            job_url = self.url
            try:
                parent = elem.find_element(By.XPATH, './ancestor::a')
                job_url = parent.get_attribute('href') or self.url
            except:
                try:
                    link = elem.find_element(By.CSS_SELECTOR, 'a')
                    job_url = link.get_attribute('href') or self.url
                except:
                    pass

            is_remote = 'remote' in title.lower() or 'remote' in location.lower()

            return {
                'title': title,
                'department': department,
                'location': location,
                'posting_date': 'Not specified',
                'remote': 'Yes' if is_remote else 'No',
                'region': self._extract_region(location),
                'url': job_url
            }

        except Exception as e:
            return None

    def _parse_job_element(self, elem, seen_urls):
        """Parse a single job element."""
        try:
            # Get URL
            href = ''
            if elem.tag_name == 'a':
                href = elem.get_attribute('href') or ''
            else:
                try:
                    link = elem.find_element(By.CSS_SELECTOR, 'a')
                    href = link.get_attribute('href') or ''
                except:
                    pass

            # Skip if already seen or not a job link
            if href in seen_urls:
                return None
            if href and '/careers/jobs/' not in href:
                return None
            if href:
                seen_urls.add(href)

            # Get title
            title = ''
            if elem.tag_name == 'a':
                title = elem.text.strip()
            else:
                for tag in ['h2', 'h3', 'h4', '.title', '.job-title', 'a']:
                    try:
                        title_elem = elem.find_element(By.CSS_SELECTOR, tag)
                        title = title_elem.text.strip()
                        if title:
                            break
                    except:
                        continue

            if not title or len(title) < 3:
                return None

            # Skip navigation items
            if any(skip in title.lower() for skip in ['search', 'filter', 'apply', 'menu', 'login']):
                return None

            # Get location
            location = 'Not specified'
            try:
                loc_elem = elem.find_element(By.CSS_SELECTOR, '[class*="location"], [class*="city"], [class*="place"]')
                location = loc_elem.text.strip()
            except:
                # Try to extract from element text
                text = elem.text
                if text:
                    lines = text.split('\n')
                    for line in lines[1:]:  # Skip first line (title)
                        line = line.strip()
                        if line and len(line) < 50:
                            location = line
                            break

            # Get department
            department = 'Not specified'
            try:
                dept_elem = elem.find_element(By.CSS_SELECTOR, '[class*="department"], [class*="category"], [class*="team"]')
                department = dept_elem.text.strip()
            except:
                pass

            is_remote = 'remote' in title.lower() or 'remote' in location.lower()

            return {
                'title': title,
                'department': department,
                'location': location,
                'posting_date': 'Not specified',
                'remote': 'Yes' if is_remote else 'No',
                'region': self._extract_region(location),
                'url': href if href else self.url
            }

        except Exception as e:
            return None

    def _parse_from_source(self):
        """Parse jobs from page source as fallback."""
        jobs = []
        seen_urls = set()

        try:
            page_source = self.driver.page_source

            # Look for job URLs and titles in the page
            # Pattern: /careers/jobs/[title]-[id]
            pattern = r'/careers/jobs/([a-z0-9-]+)-(\d+)'
            matches = re.findall(pattern, page_source, re.IGNORECASE)

            for title_slug, job_id in matches:
                url = f"https://www.3ds.com/careers/jobs/{title_slug}-{job_id}"
                if url in seen_urls:
                    continue
                seen_urls.add(url)

                # Convert slug to title
                title = title_slug.replace('-', ' ').title()

                jobs.append({
                    'title': title,
                    'department': 'Not specified',
                    'location': 'Not specified',
                    'posting_date': 'Not specified',
                    'remote': 'No',
                    'region': 'Not specified',
                    'url': url
                })

        except Exception as e:
            self.log(f"Source parsing failed: {e}", "ERROR")

        return jobs

    def _extract_region(self, location):
        """Extract region from location string."""
        location_lower = location.lower()

        # Europe
        europe = ['france', 'germany', 'uk', 'united kingdom', 'spain', 'italy', 'netherlands',
                  'belgium', 'sweden', 'norway', 'denmark', 'finland', 'poland', 'austria',
                  'switzerland', 'ireland', 'portugal', 'czech', 'hungary', 'romania']

        # Americas
        americas = ['usa', 'united states', 'us', 'canada', 'brazil', 'mexico', 'argentina']

        # APAC
        apac = ['china', 'japan', 'korea', 'india', 'singapore', 'australia', 'malaysia',
                'indonesia', 'thailand', 'vietnam', 'philippines', 'taiwan', 'hong kong']

        for country in europe:
            if country in location_lower:
                return 'EMEA'

        for country in americas:
            if country in location_lower:
                return 'Americas'

        for country in apac:
            if country in location_lower:
                return 'APAC'

        return 'Not specified'
