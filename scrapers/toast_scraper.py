"""
Toast Scraper

Scrapes job postings from Toast's careers page (Clinch Talent platform).
Uses pagination to get all jobs across multiple pages.
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from scrapers.headless_scraper import HeadlessScraper
import time
import re


class ToastScraper(HeadlessScraper):
    """Scraper for Toast careers site (Clinch Talent)."""

    def _scrape_jobs(self):
        """
        Scrape jobs from Toast using headless browser with pagination.

        Returns:
            list: List of job dictionaries
        """
        self.log("Starting Toast scrape...")

        base_url = "https://careers.toasttab.com/jobs/search"
        all_jobs = []
        seen_urls = set()
        page = 1
        max_pages = 15  # Safety limit

        while page <= max_pages:
            # Load page
            url = f"{base_url}?page={page}" if page > 1 else base_url
            self.driver.get(url)
            self.log(f"Loading page {page}: {url}")
            time.sleep(3)

            # Check for total count on first page
            if page == 1:
                try:
                    page_text = self.driver.find_element(By.TAG_NAME, 'body').text
                    match = re.search(r'of (\d+) in total', page_text)
                    if match:
                        total_jobs = int(match.group(1))
                        self.log(f"Total jobs available: {total_jobs}")
                except:
                    pass

            # Find job cards - use the specific card class
            job_cards = self.driver.find_elements(
                By.CSS_SELECTOR,
                'div.card.job-search-results-card'
            )

            if not job_cards:
                self.log(f"No job cards found on page {page}")
                break

            self.log(f"Found {len(job_cards)} job cards on page {page}")

            jobs_on_page = 0
            for card in job_cards:
                try:
                    # Find title element
                    try:
                        title_elem = card.find_element(By.CSS_SELECTOR, 'h3.card-title')
                        title = title_elem.text.strip()
                    except:
                        continue

                    if not title:
                        continue

                    # Find URL from the title link or card link
                    job_url = None
                    try:
                        link = card.find_element(By.CSS_SELECTOR, 'a[href*="/jobs/"]')
                        job_url = link.get_attribute('href')
                    except:
                        continue

                    if not job_url or job_url in seen_urls:
                        continue
                    if '/jobs/search' in job_url or '/jobs/alerts' in job_url:
                        continue

                    seen_urls.add(job_url)

                    # Find location
                    location = 'Not specified'
                    try:
                        loc_elem = card.find_element(By.CSS_SELECTOR, '.job-component-location, .job-component-list-location')
                        location = loc_elem.text.strip()
                    except:
                        pass

                    # Find department
                    department = 'Not specified'
                    try:
                        dept_elem = card.find_element(By.CSS_SELECTOR, '.job-component-department, .job-component-list-department')
                        department = dept_elem.text.strip()
                    except:
                        pass

                    job_info = {
                        'title': title,
                        'department': department,
                        'location': location,
                        'posting_date': 'Not specified',
                        'remote': 'Yes' if 'remote' in title.lower() or 'remote' in location.lower() else 'No',
                        'region': 'Not specified',
                        'url': job_url
                    }
                    all_jobs.append(job_info)
                    jobs_on_page += 1

                except Exception as e:
                    self.log(f"Error parsing job card: {e}", "WARNING")
                    continue

            self.log(f"Extracted {jobs_on_page} jobs from page {page}")

            # Check if there's a next page
            if jobs_on_page == 0:
                break

            # Check pagination - look for next page button
            try:
                # Look for pagination info
                page_text = self.driver.find_element(By.TAG_NAME, 'body').text
                match = re.search(r'Displaying \d+ - (\d+) of (\d+)', page_text)
                if match:
                    current_end = int(match.group(1))
                    total = int(match.group(2))
                    if current_end >= total:
                        self.log("Reached last page")
                        break
            except:
                pass

            page += 1

        self.log(f"Completed: {len(all_jobs)} total jobs scraped across {page} pages")
        return all_jobs
