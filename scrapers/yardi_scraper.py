"""
Yardi Scraper

Scrapes job postings from Yardi careers page.
Uses headless browser with anti-detection measures.
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from scrapers.headless_scraper import HeadlessScraper
import time
import re


class YardiScraper(HeadlessScraper):
    """Scraper for Yardi careers site."""

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
        Scrape jobs from Yardi careers page.

        Returns:
            list: List of job dictionaries
        """
        self.log("Starting Yardi scrape...")

        all_jobs = []
        seen_urls = set()

        # Load careers page
        url = self.config.get('url', 'https://careers.yardi.com/openings/')
        self.driver.get(url)
        self.log(f"Loading: {url}")
        time.sleep(8)

        # Scroll to load all jobs
        self._scroll_to_load_all()

        # Find all links on the page
        links = self.driver.find_elements(By.CSS_SELECTOR, 'a')
        self.log(f"Found {len(links)} total links")

        # Job title keywords to identify job listings
        job_keywords = ['manager', 'engineer', 'analyst', 'specialist', 'consultant',
                       'developer', 'executive', 'director', 'intern', 'coordinator',
                       'administrator', 'accountant', 'trainer', 'advisor', 'associate',
                       'representative', 'architect', 'designer', 'writer', 'recruiter']

        for link in links:
            try:
                href = link.get_attribute('href') or ''
                text = link.text.strip()

                # Skip non-job links
                if not text or len(text) < 10:
                    continue
                if '/job-posting/' not in href:
                    continue
                if href in seen_urls:
                    continue

                # Check if text contains job-like words
                text_lower = text.lower()
                if not any(keyword in text_lower for keyword in job_keywords):
                    continue

                seen_urls.add(href)

                # Parse the link text
                # Format: "Title\nLocation · Department · Division"
                lines = text.split('\n')
                title = lines[0].strip() if len(lines) > 0 else ''
                location_info = lines[1].strip() if len(lines) > 1 else ''

                if not title:
                    continue

                # Parse location info: "Location · Department · Division"
                # Handle various separators (·, ·, –, -, etc.)
                import unicodedata
                # Normalize unicode and split by common separators
                separators = ['·', '·', '–', ' - ', '�']
                parts = [location_info]
                for sep in separators:
                    if sep in location_info:
                        parts = [p.strip() for p in location_info.split(sep)]
                        break

                location = parts[0] if len(parts) > 0 else 'Not specified'
                department = parts[1] if len(parts) > 1 else 'Not specified'
                division = parts[2] if len(parts) > 2 else ''

                # Determine remote status
                is_remote = 'remote' in title.lower() or 'remote' in location.lower()

                job_info = {
                    'title': title,
                    'department': f"{department} - {division}".strip(' -') if division else department,
                    'location': location,
                    'posting_date': 'Not specified',
                    'remote': 'Yes' if is_remote else 'No',
                    'region': self._extract_region(location),
                    'url': href
                }
                all_jobs.append(job_info)

            except Exception as e:
                continue

        self.log(f"Completed: {len(all_jobs)} total jobs scraped")
        return all_jobs

    def _scroll_to_load_all(self):
        """Scroll page to load all job listings."""
        try:
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            for _ in range(10):  # Max 10 scroll attempts
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
            # Scroll back to top
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
        except Exception as e:
            self.log(f"Scroll failed: {e}", "WARNING")

    def _is_navigation(self, text):
        """Check if text is navigation/filter element."""
        nav_items = [
            'openings', 'benefits', 'culture', 'students', 'about', 'sign in',
            'all teams', 'all locations', 'search', 'client services', 'cloud & it',
            'marketing', 'operations', 'professional services', 'sales',
            'software development', 'filter'
        ]
        text_lower = text.lower()
        return any(nav in text_lower for nav in nav_items) and len(text) < 30

    def _is_location_line(self, text):
        """Check if text looks like a location line."""
        # Location patterns: City, State or City, Country
        location_patterns = [
            r'[A-Z][a-z]+,\s*[A-Z]{2}',  # City, ST
            r'[A-Z][a-z]+,\s*[A-Z][a-z]+',  # City, Country
            r'Remote',
            r'Australia', r'United Kingdom', r'Netherlands', r'Germany', r'Japan',
            r'India', r'Singapore', r'Hong Kong', r'Dubai', r'Romania', r'Canada'
        ]
        for pattern in location_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def _extract_region(self, location):
        """Extract region from location string."""
        location_lower = location.lower()

        # Americas
        us_locations = ['ga', 'tx', 'id', 'il', 'oh', 'co', 'fl', 'ny', 'ma', 'mn',
                        'ca', 'nc', 'nv', 'ut', 'az', 'd.c.', 'atlanta', 'austin',
                        'boise', 'chicago', 'cleveland', 'colorado springs', 'dallas',
                        'denver', 'irving', 'jacksonville', 'miami', 'minneapolis',
                        'new york', 'oxnard', 'raleigh', 'reno', 'salt lake',
                        'san diego', 'san francisco', 'santa ana', 'santa barbara',
                        'scottsdale', 'waltham', 'washington', 'westchester', 'westford',
                        'remote – us', 'remote - us']

        canada_locations = ['sk', 'on', 'bc', 'saskatoon', 'toronto', 'vancouver',
                           'remote – canada', 'remote - canada']

        # APAC
        apac_locations = ['hong kong', 'pune', 'india', 'shanghai', 'china',
                         'singapore', 'tokyo', 'japan', 'melbourne', 'sydney',
                         'australia']

        # EMEA
        emea_locations = ['amsterdam', 'netherlands', 'krakow', 'london',
                         'united kingdom', 'mainz', 'germany', 'milton keynes',
                         'stirling', 'scotland', 'dubai', 'arab emirates',
                         'remote – romania', 'remote - romania']

        for loc in us_locations:
            if loc in location_lower:
                return 'Americas'

        for loc in canada_locations:
            if loc in location_lower:
                return 'Americas'

        for loc in apac_locations:
            if loc in location_lower:
                return 'APAC'

        for loc in emea_locations:
            if loc in location_lower:
                return 'EMEA'

        return 'Not specified'
