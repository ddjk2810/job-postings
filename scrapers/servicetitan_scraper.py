#!/usr/bin/env python3
"""
ServiceTitan Job Scraper (Headless Browser)

Scrapes job postings from ServiceTitan's Workday-hosted careers page.
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .headless_scraper import HeadlessScraper
import time


class ServiceTitanScraper(HeadlessScraper):
    """Scraper for ServiceTitan careers page."""

    def _scrape_jobs(self):
        """
        Scrape jobs from ServiceTitan's Workday page.

        Returns:
            list: List of job dictionaries
        """
        self.log("Starting ServiceTitan scrape...")
        jobs = []

        # Load the careers page
        self.driver.get(self.url)
        time.sleep(5)  # Wait for initial page load and JS to execute
        self.log(f"Loaded page: {self.url}")

        # Wait for job listings to load
        # Try multiple Workday selectors as the structure can vary
        self.log("Waiting for job listings to load...")

        job_elements = []
        selectors = [
            'li[data-automation-id="jobPostingItem"]',
            'div[data-automation-id="jobPostingItem"]',
            'a[data-automation-id="jobTitle"]',
            'li.css-1q2dra3',  # Common Workday class
            'a[href*="/job/"]',
        ]

        for selector in selectors:
            try:
                elements = self.wait_for_elements(By.CSS_SELECTOR, selector, timeout=15)
                if elements and len(elements) > 0:
                    # If we found title links directly, get parent elements
                    if selector == 'a[data-automation-id="jobTitle"]':
                        job_elements = [elem.find_element(By.XPATH, './ancestor::li') for elem in elements]
                    else:
                        job_elements = elements
                    self.log(f"Found {len(job_elements)} job elements using selector: {selector}")
                    break
            except:
                continue

        if not job_elements:
            self.log("Could not find job elements with any selector", level="WARNING")
            return []

        self.log(f"Found {len(job_elements)} job elements")

        # Extract job data from each element
        seen_jobs = set()
        for element in job_elements:
            try:
                # Extract title and URL - try multiple selectors
                title = ""
                url = ""
                title_selectors = [
                    'a[data-automation-id="jobTitle"]',
                    'a[href*="/job/"]',
                    'h3 a',
                    'a'
                ]
                for sel in title_selectors:
                    try:
                        title_elem = element.find_element(By.CSS_SELECTOR, sel)
                        title = title_elem.text.strip()
                        url = title_elem.get_attribute('href')
                        if title and url:
                            break
                    except:
                        continue

                if not title:
                    continue

                # Extract location - try multiple selectors
                location = ""
                location_selectors = [
                    'dd[data-automation-id="jobPostingLocation"]',
                    'span[data-automation-id="location"]',
                    'div[class*="location"]'
                ]
                for sel in location_selectors:
                    try:
                        location_elem = element.find_element(By.CSS_SELECTOR, sel)
                        location = location_elem.text.strip()
                        if location:
                            break
                    except:
                        continue

                # Extract posting date
                posting_date = ""
                try:
                    date_elem = element.find_element(By.CSS_SELECTOR, 'dd[data-automation-id="postedOn"]')
                    posting_date = date_elem.text.strip()
                except:
                    pass

                # Create unique identifier
                job_id = (title, location)
                if job_id in seen_jobs:
                    continue

                seen_jobs.add(job_id)

                # Determine if remote
                is_remote = 'Remote' in location or 'remote' in location.lower() if location else False

                jobs.append({
                    'title': title,
                    'department': '',  # Workday doesn't always show department on list view
                    'location': location,
                    'posting_date': posting_date,
                    'remote': 'Yes' if is_remote else 'No',
                    'region': self._extract_region(location),
                    'url': url
                })

            except Exception as e:
                self.log(f"Error parsing job element: {e}", level="WARNING")
                continue

        self.log(f"Completed: {len(jobs)} unique jobs scraped")
        return jobs

    def _extract_region(self, location):
        """
        Extract region/country from location string.

        Args:
            location (str): Location string

        Returns:
            str: Region/country
        """
        if not location:
            return ''

        # Common patterns
        if 'Remote' in location:
            # Try to extract country from remote location
            if 'United States' in location or 'USA' in location or 'US' in location:
                return 'United States'
            elif 'Canada' in location:
                return 'Canada'
            else:
                return 'Remote'

        # Extract last part (usually country)
        parts = location.split(',')
        if parts:
            return parts[-1].strip()

        return location
