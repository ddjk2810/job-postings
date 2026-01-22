"""
Simulations Plus Scraper

Scrapes job postings from Simulations Plus careers page.
The page loads jobs dynamically via JavaScript.
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from scrapers.headless_scraper import HeadlessScraper
import time
import re
import json


class SimulationsPlusScraper(HeadlessScraper):
    """Scraper for Simulations Plus careers site."""

    def _scrape_jobs(self):
        """
        Scrape jobs from Simulations Plus using headless browser.

        Returns:
            list: List of job dictionaries
        """
        self.log("Starting Simulations Plus scrape...")

        all_jobs = []
        seen_titles = set()

        # Load careers page
        url = self.config.get('url', 'https://www.simulations-plus.com/career-center/')
        self.driver.get(url)
        self.log(f"Loading: {url}")
        time.sleep(5)  # Wait for dynamic content

        # Scroll down to trigger lazy loading
        self._scroll_page()

        # Try multiple methods to find job listings
        job_methods = [
            self._find_jobs_via_links,
            self._find_jobs_via_divs,
            self._find_jobs_via_list,
            self._find_jobs_via_iframe,
            self._extract_from_page_text,
        ]

        for method in job_methods:
            try:
                jobs = method()
                if jobs:
                    self.log(f"Found {len(jobs)} jobs via {method.__name__}")
                    for job in jobs:
                        title_key = job['title'].lower()
                        if title_key not in seen_titles:
                            seen_titles.add(title_key)
                            all_jobs.append(job)
                    break
            except Exception as e:
                self.log(f"Method {method.__name__} failed: {e}", "WARNING")
                continue

        self.log(f"Completed: {len(all_jobs)} total jobs scraped")
        return all_jobs

    def _scroll_page(self):
        """Scroll page to trigger lazy loading."""
        try:
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            for _ in range(3):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
            # Scroll back up
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
        except:
            pass

    def _find_jobs_via_links(self):
        """Find jobs via link elements."""
        jobs = []

        # Common selectors for job links
        selectors = [
            'a[href*="job"]',
            'a[href*="career"]',
            'a[href*="position"]',
            'a[href*="opening"]',
            '.job-listing a',
            '.careers a',
            '#jobopenings a',
            'div[id*="job"] a',
        ]

        for selector in selectors:
            try:
                links = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for link in links:
                    text = link.text.strip()
                    href = link.get_attribute('href') or ''

                    if not text or len(text) < 5:
                        continue

                    # Skip non-job links
                    if any(skip in text.lower() for skip in ['apply now', 'submit', 'learn more', 'contact', 'home', 'about']):
                        continue

                    job_info = self._create_job_entry(text, href)
                    if job_info:
                        jobs.append(job_info)

            except:
                continue

        return jobs

    def _find_jobs_via_divs(self):
        """Find jobs via div elements."""
        jobs = []

        selectors = [
            'div[class*="job"]',
            'div[class*="career"]',
            'div[class*="position"]',
            'article[class*="job"]',
            '.job-card',
            '.job-item',
            '.opening',
        ]

        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements:
                    # Try to find title
                    title = None
                    for tag in ['h2', 'h3', 'h4', '.title', 'a']:
                        try:
                            title_elem = elem.find_element(By.CSS_SELECTOR, tag)
                            title = title_elem.text.strip()
                            if title and len(title) > 3:
                                break
                        except:
                            continue

                    if not title:
                        continue

                    # Try to find link
                    href = ''
                    try:
                        link = elem.find_element(By.CSS_SELECTOR, 'a')
                        href = link.get_attribute('href') or ''
                    except:
                        pass

                    job_info = self._create_job_entry(title, href)
                    if job_info:
                        jobs.append(job_info)

            except:
                continue

        return jobs

    def _find_jobs_via_list(self):
        """Find jobs via list elements."""
        jobs = []

        selectors = [
            'ul[class*="job"] li',
            'ul[class*="career"] li',
            'ol[class*="job"] li',
            '#job-list li',
            '.job-listings li',
        ]

        for selector in selectors:
            try:
                items = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for item in items:
                    text = item.text.strip()
                    if not text or len(text) < 5:
                        continue

                    # Get first line as title
                    lines = text.split('\n')
                    title = lines[0].strip()

                    href = ''
                    try:
                        link = item.find_element(By.CSS_SELECTOR, 'a')
                        href = link.get_attribute('href') or ''
                    except:
                        pass

                    job_info = self._create_job_entry(title, href)
                    if job_info:
                        jobs.append(job_info)

            except:
                continue

        return jobs

    def _find_jobs_via_iframe(self):
        """Find jobs via embedded iframe."""
        jobs = []

        try:
            iframes = self.driver.find_elements(By.TAG_NAME, 'iframe')
            for iframe in iframes:
                src = iframe.get_attribute('src') or ''

                # Check for common job board iframes
                if any(platform in src.lower() for platform in ['bamboohr', 'greenhouse', 'lever', 'workday', 'jobvite']):
                    self.log(f"Found job platform iframe: {src}")
                    self.driver.switch_to.frame(iframe)
                    time.sleep(2)

                    # Try to find jobs in iframe
                    links = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="job"]')
                    for link in links:
                        text = link.text.strip()
                        href = link.get_attribute('href') or ''
                        job_info = self._create_job_entry(text, href)
                        if job_info:
                            jobs.append(job_info)

                    self.driver.switch_to.default_content()
                    break

        except Exception as e:
            self.log(f"Iframe search failed: {e}", "WARNING")
            try:
                self.driver.switch_to.default_content()
            except:
                pass

        return jobs

    def _extract_from_page_text(self):
        """Extract jobs from page text as last resort."""
        jobs = []

        try:
            page_text = self.driver.find_element(By.TAG_NAME, 'body').text

            # Look for common job title patterns
            job_patterns = [
                r'(?:Senior|Jr\.|Junior|Lead|Principal|Staff)\s+[\w\s]+(?:Engineer|Developer|Scientist|Analyst|Manager)',
                r'[\w\s]+(?:Engineer|Developer|Scientist|Analyst|Manager|Director|VP|Architect)',
            ]

            for pattern in job_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                for match in matches:
                    title = match.strip()
                    if len(title) > 10 and len(title) < 100:
                        job_info = self._create_job_entry(title, '')
                        if job_info:
                            jobs.append(job_info)

        except Exception as e:
            self.log(f"Text extraction failed: {e}", "WARNING")

        return jobs

    def _create_job_entry(self, title, url):
        """Create a standardized job entry."""
        if not title or len(title) < 5:
            return None

        # Skip obvious non-job titles
        skip_words = ['apply', 'submit', 'learn', 'contact', 'home', 'about', 'menu', 'search', 'login', 'sign']
        if any(word in title.lower() for word in skip_words):
            return None

        is_remote = 'remote' in title.lower()

        return {
            'title': title,
            'department': 'Not specified',
            'location': 'Remote' if is_remote else 'Not specified',
            'posting_date': 'Not specified',
            'remote': 'Yes' if is_remote else 'No',
            'region': 'Americas',  # Simulations Plus is US-based
            'url': url if url else self.url
        }
