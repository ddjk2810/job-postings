"""
Kinaxis Scraper

Scrapes job postings from Kinaxis's iCIMS careers page using headless browser.
"""

from selenium.webdriver.common.by import By
from scrapers.headless_scraper import HeadlessScraper
import time


class KinaxisScraper(HeadlessScraper):
    """Scraper for Kinaxis careers site (iCIMS platform)."""

    def _scrape_jobs(self):
        """
        Scrape jobs from Kinaxis using headless browser.

        Returns:
            list: List of job dictionaries
        """
        self.log("Starting Kinaxis scrape...")

        # iCIMS loads job content in an iframe - load the page
        iframe_url = self.url.rstrip('/') + '/jobs/search?in_iframe=1'
        self.driver.get(iframe_url)
        self.log(f"Loaded page: {iframe_url}")

        # Wait for page to load
        time.sleep(8)  # iCIMS can be slow to load

        # Switch to the iCIMS content iframe
        self.log("Looking for iCIMS content iframe...")
        try:
            iframe = self.driver.find_element(By.ID, 'icims_content_iframe')
            self.driver.switch_to.frame(iframe)
            self.log("Switched to icims_content_iframe")
            time.sleep(5)  # Wait for iframe content to load
        except Exception as e:
            self.log(f"Could not find/switch to iframe: {e}", "WARNING")

        # Wait for job listings
        self.log("Waiting for job listings to load...")

        # iCIMS uses links with /jobs/ in href for job listings
        job_links = self.wait_for_elements(
            By.CSS_SELECTOR,
            'a[href*="/jobs/"]',
            timeout=15
        )

        if not job_links:
            self.log("Could not find job listings", "ERROR")
            return []

        self.log(f"Found {len(job_links)} job link elements")

        jobs = []
        seen_urls = set()

        # Valid departments list
        valid_departments = ['Consulting', 'Engineering', 'Finance', 'Marketing', 
                           'Customer Service', 'Sales', 'Information Technology', 
                           'Product Management', 'Business Development', 'Strategy/Planning']

        for link in job_links:
            try:
                url = link.get_attribute('href')
                
                # Skip search URLs and already seen URLs
                if not url or 'search' in url or url in seen_urls:
                    continue
                
                # Get the raw title text and clean it
                raw_title = link.text.strip()
                if not raw_title:
                    continue
                
                # Clean up title - remove "Title\n" prefix if present
                title_lines = raw_title.split('\n')
                title = title_lines[-1].strip() if title_lines else raw_title
                if title.lower() == 'title':
                    continue  # Skip header row
                    
                seen_urls.add(url)

                # Try to find location and department by traversing the DOM
                location = 'Not specified'
                department = 'Not specified'
                remote = 'No'
                posting_date = 'Not specified'

                try:
                    # Navigate up to find the job container
                    parent = link
                    for _ in range(6):  # Try up to 6 levels up
                        try:
                            parent = parent.find_element(By.XPATH, './..')
                            parent_text = parent.text
                            
                            # Check if this parent contains job metadata
                            if 'Category' in parent_text or 'Location' in parent_text:
                                lines = parent_text.split('\n')
                                
                                for i, line in enumerate(lines):
                                    line_stripped = line.strip()
                                    line_lower = line_stripped.lower()
                                    
                                    # Extract location from Location field or location patterns
                                    if line_lower == 'location' and i + 1 < len(lines):
                                        next_line = lines[i + 1].strip()
                                        if next_line and location == 'Not specified':
                                            location = next_line
                                    
                                    # Extract category/department
                                    if line_lower == 'category' and i + 1 < len(lines):
                                        next_line = lines[i + 1].strip()
                                        if next_line in valid_departments and department == 'Not specified':
                                            department = next_line
                                    elif line_stripped in valid_departments and department == 'Not specified':
                                        department = line_stripped
                                    
                                    # Check for remote status
                                    if line_lower == 'remote yes':
                                        remote = 'Yes'
                                    elif line_lower == 'remote no':
                                        remote = 'No'
                                    elif line_lower.startswith('remote') and i + 1 < len(lines):
                                        next_line = lines[i + 1].strip().lower()
                                        if next_line == 'yes':
                                            remote = 'Yes'
                                        elif next_line == 'no':
                                            remote = 'No'
                                        
                                    # Extract posting date
                                    if 'days ago' in line_lower or 'posted today' in line_lower:
                                        posting_date = line_stripped
                                    elif 'posted date' in line_lower and i + 1 < len(lines):
                                        next_line = lines[i + 1].strip()
                                        if 'ago' in next_line.lower() or '/' in next_line:
                                            posting_date = next_line
                                
                                break  # Found the container with job info
                        except:
                            continue
                except Exception as e:
                    pass

                # Check if remote is in title or location
                if remote == 'No' and ('remote' in title.lower() or 'remote' in location.lower()):
                    remote = 'Yes'

                job_info = {
                    'title': title,
                    'department': department,
                    'location': location,
                    'posting_date': posting_date,
                    'remote': remote,
                    'region': 'Not specified',
                    'url': url
                }
                jobs.append(job_info)

            except Exception as e:
                self.log(f"Error parsing job link: {e}", "WARNING")
                continue

        self.log(f"Completed: {len(jobs)} unique jobs scraped")
        return jobs
