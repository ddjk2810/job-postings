"""
Tyler Technologies Scraper

Scrapes job postings from Tyler Technologies careers page.
Uses Jobvite integration embedded in their custom careers site.
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from scrapers.headless_scraper import HeadlessScraper
import time
import re


class TylerScraper(HeadlessScraper):
    """Scraper for Tyler Technologies careers site (Jobvite)."""

    def _setup_driver(self):
        """Set up Chrome driver with anti-detection measures."""
        if self.driver:
            return

        self.log("Setting up headless Chrome browser with anti-detection...")

        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager

        chrome_options = Options()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)

            # Override webdriver detection
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    })
                '''
            })

            self.log("Browser ready")
        except Exception as e:
            self.log(f"Failed to setup browser: {e}", "ERROR")
            raise

    def _scrape_jobs(self):
        """
        Scrape jobs from Tyler Technologies using headless browser.

        Returns:
            list: List of job dictionaries
        """
        self.log("Starting Tyler Technologies scrape...")

        all_jobs = []
        seen_urls = set()

        # Tyler uses their own careers page with Jobvite
        base_url = "https://www.tylertech.com/careers/job-listings"

        self.driver.get(base_url)
        self.log(f"Loading: {base_url}")
        time.sleep(5)  # Wait for page to fully load including Jobvite iframe

        # Try to find job listings in various formats
        jobs_found = False

        # Method 1: Look for Jobvite iframe and switch to it
        try:
            iframes = self.driver.find_elements(By.TAG_NAME, 'iframe')
            for iframe in iframes:
                name = iframe.get_attribute('name') or ''
                src = iframe.get_attribute('src') or ''
                if 'jobvite' in name.lower() or 'jobvite' in src.lower() or 'jv-' in name.lower():
                    self.log(f"Found Jobvite iframe: {name or src}")
                    self.driver.switch_to.frame(iframe)
                    time.sleep(2)
                    jobs_found = True
                    break
        except Exception as e:
            self.log(f"No iframe found: {e}", "WARNING")

        # Method 2: Try to find job listings directly on the page
        job_selectors = [
            'div[class*="job-listing"]',
            'div[class*="job-card"]',
            'div[class*="career"]',
            'tr[class*="job"]',
            'a[href*="/job/"]',
            'a[href*="jobs.jobvite.com"]',
            '.jv-job-list a',
            'ul.job-listings li',
            'div.job-openings a',
        ]

        for selector in job_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    self.log(f"Found {len(elements)} elements with selector: {selector}")
                    jobs_found = True
                    break
            except:
                continue

        # Parse jobs from page content
        try:
            # Get page source and find job data
            page_source = self.driver.page_source

            # Look for job links with titles
            # Tyler format: job title as link text with href to job details
            job_links = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="/careers/job-openings/"]')

            if not job_links:
                job_links = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="/job-listings/"]')

            if not job_links:
                # Try broader selector
                job_links = self.driver.find_elements(By.CSS_SELECTOR, 'a')

            self.log(f"Found {len(job_links)} potential job links")

            for link in job_links:
                try:
                    href = link.get_attribute('href') or ''
                    text = link.text.strip()

                    # Skip non-job links
                    if not text or len(text) < 5:
                        continue
                    if not href:
                        continue

                    # Filter to actual job links
                    if '/careers/job-openings/' not in href.lower() and '/job/' not in href.lower():
                        continue

                    # Skip navigation links
                    if any(skip in text.lower() for skip in ['search', 'filter', 'all jobs', 'apply', 'view all']):
                        continue

                    if href in seen_urls:
                        continue
                    seen_urls.add(href)

                    # Try to get location from parent element
                    location = 'Not specified'
                    try:
                        parent = link.find_element(By.XPATH, './..')
                        parent_text = parent.text
                        # Look for location pattern (City, State or City, Country)
                        loc_match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z]{2}(?:\s+\d{5})?)', parent_text)
                        if loc_match:
                            location = loc_match.group(1)
                    except:
                        pass

                    # Try alternate location extraction
                    if location == 'Not specified':
                        try:
                            parent = link.find_element(By.XPATH, './ancestor::div[contains(@class,"job") or contains(@class,"listing")]')
                            loc_elem = parent.find_element(By.CSS_SELECTOR, '[class*="location"], [class*="city"]')
                            location = loc_elem.text.strip()
                        except:
                            pass

                    is_remote = 'remote' in text.lower() or 'remote' in location.lower()

                    job_info = {
                        'title': text,
                        'department': 'Not specified',
                        'location': location,
                        'posting_date': 'Not specified',
                        'remote': 'Yes' if is_remote else 'No',
                        'region': self._extract_region(location),
                        'url': href
                    }
                    all_jobs.append(job_info)

                except Exception as e:
                    continue

        except Exception as e:
            self.log(f"Error parsing jobs: {e}", "ERROR")

        # Switch back to main content if we were in an iframe
        try:
            self.driver.switch_to.default_content()
        except:
            pass

        # If no jobs found via links, try parsing structured data
        if len(all_jobs) == 0:
            self.log("No jobs found via links, trying alternative methods...")
            all_jobs = self._try_alternative_parsing()

        self.log(f"Completed: {len(all_jobs)} total jobs scraped")
        return all_jobs

    def _try_alternative_parsing(self):
        """Try alternative methods to parse job listings from text content."""
        jobs = []
        seen_titles = set()

        try:
            # Get page text content
            page_text = self.driver.find_element(By.TAG_NAME, 'body').text

            # Tyler's page shows job titles followed by location on next line
            # Pattern: Title\nLocation (City, State or Remote | City, State)
            lines = page_text.split('\n')

            i = 0
            while i < len(lines) - 1:
                line = lines[i].strip()

                # Skip short lines and navigation items
                if len(line) < 5 or any(skip in line.lower() for skip in
                    ['login', 'register', 'search', 'solutions', 'resources', 'about', 'careers', 'support', 'press alt']):
                    i += 1
                    continue

                # Check if this looks like a job title
                # Job titles typically don't start with common non-job words
                if line and not line.startswith(('In this', 'As a', 'Join', 'Are you', 'This position', 'The', 'Meet our')):
                    # Check next line for location pattern
                    next_line = lines[i + 1].strip() if i + 1 < len(lines) else ''

                    # Location patterns: City, State or Remote | City, State
                    loc_pattern = r'^(Remote\s*\|?\s*)?([A-Z][a-zA-Z\s]+,\s*[A-Z][a-zA-Z\s]+)$'
                    loc_match = re.match(loc_pattern, next_line)

                    if loc_match:
                        title = line
                        location = next_line

                        # Skip duplicates
                        title_key = title.lower()
                        if title_key in seen_titles:
                            i += 2
                            continue
                        seen_titles.add(title_key)

                        is_remote = 'remote' in title.lower() or 'remote' in location.lower()

                        jobs.append({
                            'title': title,
                            'department': 'Not specified',
                            'location': location.replace('Remote | ', '').strip(),
                            'posting_date': 'Not specified',
                            'remote': 'Yes' if is_remote else 'No',
                            'region': self._extract_region(location),
                            'url': self.url
                        })
                        i += 2
                        continue

                i += 1

        except Exception as e:
            self.log(f"Alternative parsing failed: {e}", "WARNING")

        return jobs

    def _extract_region(self, location):
        """Extract region from location string."""
        location_lower = location.lower()

        # US states
        us_states = ['al', 'ak', 'az', 'ar', 'ca', 'co', 'ct', 'de', 'fl', 'ga', 'hi', 'id', 'il', 'in', 'ia',
                     'ks', 'ky', 'la', 'me', 'md', 'ma', 'mi', 'mn', 'ms', 'mo', 'mt', 'ne', 'nv', 'nh', 'nj',
                     'nm', 'ny', 'nc', 'nd', 'oh', 'ok', 'or', 'pa', 'ri', 'sc', 'sd', 'tn', 'tx', 'ut', 'vt',
                     'va', 'wa', 'wv', 'wi', 'wy', 'maine', 'texas', 'ohio', 'colorado', 'virginia']

        for state in us_states:
            if state in location_lower or f', {state}' in location_lower:
                return 'Americas'

        if 'canada' in location_lower or ', on' in location_lower or ', bc' in location_lower:
            return 'Americas'

        if 'philippines' in location_lower or 'manila' in location_lower:
            return 'APAC'

        if 'australia' in location_lower:
            return 'APAC'

        if 'uk' in location_lower or 'united kingdom' in location_lower:
            return 'EMEA'

        return 'Not specified'
