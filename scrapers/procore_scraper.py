"""
Procore Scraper

Scrapes job postings from Procore's careers page.
Uses pagination to get all jobs across multiple pages.
"""

from selenium.webdriver.common.by import By
from scrapers.headless_scraper import HeadlessScraper
import time
import re


class ProcoreScraper(HeadlessScraper):
    """Scraper for Procore careers site."""

    def _scrape_jobs(self):
        """
        Scrape jobs from Procore using headless browser with pagination.

        Returns:
            list: List of job dictionaries
        """
        self.log("Starting Procore scrape...")

        base_url = "https://careers.procore.com/jobs/search"
        all_jobs = []
        seen_urls = set()
        page = 1
        max_pages = 10  # Safety limit
        total_jobs = None

        while page <= max_pages:
            # Load page
            url = f"{base_url}?page={page}" if page > 1 else base_url
            self.driver.get(url)
            self.log(f"Loading page {page}: {url}")
            time.sleep(4)

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

            # Find job links - Procore uses direct links to job pages
            job_links = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="/jobs/"]')

            if not job_links:
                self.log(f"No job links found on page {page}")
                break

            self.log(f"Found {len(job_links)} job link elements on page {page}")

            # Get body text for extracting location/department info
            body_text = self.driver.find_element(By.TAG_NAME, 'body').text
            lines = body_text.split('\n')

            jobs_on_page = 0
            for link in job_links:
                try:
                    job_url = link.get_attribute('href')
                    title = link.text.strip()

                    # Skip invalid links
                    if not job_url or not title:
                        continue
                    if '/jobs/search' in job_url or '/jobs/alerts' in job_url:
                        continue
                    if job_url in seen_urls:
                        continue
                    if len(title) < 5:
                        continue

                    seen_urls.add(job_url)

                    # Find location and department from body text
                    location = 'Not specified'
                    department = 'Not specified'

                    # Look for the job title in the text and get the next values
                    for i, line in enumerate(lines):
                        if title in line and i + 2 < len(lines):
                            # Usually format is: Title, Location, Department
                            next_line = lines[i + 1].strip() if i + 1 < len(lines) else ''
                            next_next = lines[i + 2].strip() if i + 2 < len(lines) else ''

                            # Check if next line looks like a location
                            if next_line and len(next_line) < 50 and not next_line.startswith('Mid-') and not next_line.startswith('Senior'):
                                location = next_line

                            # Check if the line after looks like a department
                            if next_next and len(next_next) < 50:
                                department = next_next
                            break

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
                    self.log(f"Error parsing job link: {e}", "WARNING")
                    continue

            self.log(f"Extracted {jobs_on_page} jobs from page {page}")

            # Check if we've got all jobs
            if total_jobs and len(all_jobs) >= total_jobs:
                self.log("Got all jobs")
                break

            # Check if there's a next page
            if jobs_on_page == 0:
                break

            # Check pagination
            try:
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
