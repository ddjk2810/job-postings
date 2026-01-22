"""
AppFolio Scraper

Scrapes job postings from AppFolio's careers page using headless browser.
Jobs are loaded via a Jobvite iframe embedded in the page.
"""

from selenium.webdriver.common.by import By
from scrapers.headless_scraper import HeadlessScraper
import time


class AppFolioScraper(HeadlessScraper):
    """Scraper for AppFolio careers site (Jobvite iframe)."""

    def _scrape_jobs(self):
        """
        Scrape jobs from AppFolio using headless browser.
        Jobs are in a Jobvite iframe that needs to be switched to.

        Returns:
            list: List of job dictionaries
        """
        self.log("Starting AppFolio scrape...")

        # Use the jobs page URL
        url = "https://www.appfolio.com/open-roles?p=jobs"
        self.driver.get(url)
        self.log(f"Loaded page: {url}")

        # Wait for page and iframe to load
        time.sleep(5)

        # Find and switch to the Jobvite iframe
        self.log("Looking for Jobvite iframe...")
        iframes = self.driver.find_elements(By.TAG_NAME, 'iframe')

        jobvite_iframe = None
        for iframe in iframes:
            src = iframe.get_attribute('src') or ''
            if 'jobvite' in src.lower():
                jobvite_iframe = iframe
                self.log(f"Found Jobvite iframe: {src[:80]}")
                break

        if not jobvite_iframe:
            self.log("Could not find Jobvite iframe", "ERROR")
            return []

        # Switch to the iframe
        self.driver.switch_to.frame(jobvite_iframe)
        self.log("Switched to Jobvite iframe")
        time.sleep(3)

        # Wait for job listings inside iframe
        self.log("Waiting for job listings to load...")
        job_elements = self.wait_for_elements(
            By.CSS_SELECTOR,
            '.jv-job-list-name',
            timeout=15
        )

        if not job_elements:
            # Try alternative Jobvite selectors
            job_elements = self.wait_for_elements(
                By.CSS_SELECTOR,
                'a[href*="/job/"]',
                timeout=10
            )

        if not job_elements:
            self.log("Could not find job listings in iframe", "ERROR")
            return []

        self.log(f"Found {len(job_elements)} job elements")

        jobs = []
        seen_titles = set()

        for element in job_elements:
            try:
                # Extract job information
                title = element.text.strip()

                # Skip if just location info
                if not title or 'Location' in title:
                    continue

                # Get only the job title (first line if multi-line)
                title_lines = title.split('\n')
                title = title_lines[0].strip()

                if not title:
                    continue

                # Avoid duplicates
                if title in seen_titles:
                    continue
                seen_titles.add(title)

                # Try to get the URL
                url = element.get_attribute('href') or ''
                if not url:
                    try:
                        link = element.find_element(By.XPATH, './/ancestor::a | .//a')
                        url = link.get_attribute('href') or ''
                    except:
                        pass

                # Try to find location
                location = 'Not specified'
                try:
                    parent = element.find_element(By.XPATH, './ancestor::tr | ./ancestor::div[contains(@class,"jv-job")]')
                    loc_elem = parent.find_element(By.CSS_SELECTOR, '.jv-job-list-location, [class*="location"]')
                    location = loc_elem.text.strip()
                except:
                    # Check if location is in the remaining lines
                    if len(title_lines) > 1:
                        location = title_lines[-1].strip()

                # Try to find department
                department = 'Not specified'
                try:
                    parent = element.find_element(By.XPATH, './ancestor::tr | ./ancestor::div[contains(@class,"jv-job")]')
                    dept_elem = parent.find_element(By.CSS_SELECTOR, '.jv-job-list-department, [class*="department"], [class*="category"]')
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
                    'url': url
                }
                jobs.append(job_info)

            except Exception as e:
                self.log(f"Error parsing job element: {e}", "WARNING")
                continue

        # Switch back to main content
        self.driver.switch_to.default_content()

        self.log(f"Completed: {len(jobs)} jobs scraped")
        return jobs
