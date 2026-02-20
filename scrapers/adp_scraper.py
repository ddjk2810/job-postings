"""
ADP Workforce Now Scraper

Scrapes job postings from ADP Workforce Now career portals.
ADP is a heavy JavaScript SPA that requires a headless browser.
"""

from selenium.webdriver.common.by import By
from scrapers.headless_scraper import HeadlessScraper
import time


class ADPScraper(HeadlessScraper):
    """Scraper for ADP Workforce Now career sites."""

    def _scrape_jobs(self):
        """
        Scrape jobs from ADP Workforce Now using headless browser.

        Returns:
            list: List of job dictionaries
        """
        self.log("Starting ADP scrape...")

        self.driver.get(self.url)
        self.log(f"Loaded page: {self.url}")

        # ADP is a heavy SPA - give it time to render
        time.sleep(10)

        # Wait for job listings to appear
        job_cards = self.wait_for_elements(
            By.CSS_SELECTOR,
            '[class*="job"], [class*="posting"], [class*="requisition"], a[href*="job"]',
            timeout=20
        )

        if not job_cards:
            self.log("No job cards found on page", "WARNING")
            # Try scrolling to trigger lazy loading
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(5)
            job_cards = self.wait_for_elements(
                By.CSS_SELECTOR,
                '[class*="job"], [class*="posting"], [class*="requisition"], a[href*="job"]',
                timeout=10
            )

        if not job_cards:
            self.log("Could not find job listings", "ERROR")
            return []

        self.log(f"Found {len(job_cards)} job card elements")

        jobs = []
        seen_titles = set()

        for card in job_cards:
            try:
                # Extract title
                title = ''
                for selector in ['h2', 'h3', 'h4', '[class*="title"]', '[class*="name"]']:
                    try:
                        el = card.find_element(By.CSS_SELECTOR, selector)
                        title = el.text.strip()
                        if title:
                            break
                    except Exception:
                        continue

                if not title:
                    title = card.text.strip().split('\n')[0]

                if not title or title in seen_titles:
                    continue
                seen_titles.add(title)

                # Extract location
                location = 'Not specified'
                for selector in ['[class*="location"]', '[class*="city"]']:
                    try:
                        el = card.find_element(By.CSS_SELECTOR, selector)
                        location = el.text.strip()
                        if location:
                            break
                    except Exception:
                        continue

                # Extract URL
                job_url = ''
                try:
                    if card.tag_name == 'a':
                        job_url = card.get_attribute('href')
                    else:
                        link = card.find_element(By.TAG_NAME, 'a')
                        job_url = link.get_attribute('href')
                except Exception:
                    pass

                remote = 'Yes' if 'remote' in location.lower() or 'remote' in title.lower() else 'No'

                jobs.append({
                    'title': title,
                    'department': 'Not specified',
                    'location': location,
                    'posting_date': 'Not specified',
                    'remote': remote,
                    'region': 'Not specified',
                    'url': job_url or self.url
                })
            except Exception as e:
                self.log(f"Error parsing job card: {e}", "WARNING")
                continue

        self.log(f"Completed: {len(jobs)} jobs scraped")
        return jobs
