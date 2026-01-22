#!/usr/bin/env python3
"""
Dayforce HCM Job Scraper (Headless Browser)

Scrapes job postings from Dayforce HCM career portals.
Optimized for speed with better selectors and location extraction.
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .headless_scraper import HeadlessScraper
import time
import re


class DayforceScraper(HeadlessScraper):
    """Scraper for Dayforce HCM career portals (uses Ant Design)."""

    def _scrape_jobs(self):
        """
        Scrape jobs from Dayforce HCM portal.

        Returns:
            list: List of job dictionaries
        """
        self.log("Starting Dayforce HCM scrape...")
        jobs = []

        # Load the careers page
        self.driver.get(self.url)
        time.sleep(8)  # Dayforce needs time to load React content
        self.log(f"Loaded page: {self.url}")

        # Wait for job listings to load
        self.log("Waiting for job listings to load...")

        # Dayforce uses Ant Design - try ant-card first, then fallback to job links
        job_cards = []

        # Try Ant Design card selector first (faster)
        try:
            job_cards = self.wait_for_elements(By.CSS_SELECTOR, '.ant-card', timeout=5)
            if job_cards:
                self.log(f"Found {len(job_cards)} Ant Design cards")
        except:
            pass

        # If no cards, fallback to job links
        if not job_cards:
            try:
                job_links = self.wait_for_elements(By.CSS_SELECTOR, 'a[href*="/jobs/"]', timeout=10)
                if job_links:
                    self.log(f"Found {len(job_links)} job links")
                    return self._extract_from_links(job_links)
            except:
                pass

        if not job_cards:
            self.log("No job elements found", level="WARNING")
            return []

        # Get page text for location extraction
        body_text = self.driver.find_element(By.TAG_NAME, 'body').text

        # Extract job data from cards
        seen_urls = set()
        for card in job_cards:
            try:
                # Get card text
                card_text = card.text.strip()
                if not card_text or len(card_text) < 5:
                    continue

                # Find job link in card
                url = ''
                title = ''
                try:
                    links = card.find_elements(By.CSS_SELECTOR, 'a[href*="/jobs/"]')
                    for link in links:
                        link_text = link.text.strip()
                        link_url = link.get_attribute('href')
                        # Skip "Read More" links
                        if link_text and link_text.lower() != 'read more' and link_url:
                            title = link_text
                            url = link_url
                            break
                except:
                    pass

                if not title or not url:
                    continue

                if url in seen_urls:
                    continue
                seen_urls.add(url)

                # Extract location from card text
                location = self._extract_location_from_text(card_text)

                # Extract department if present
                department = ''

                # Determine if remote
                is_remote = 'remote' in title.lower() or 'remote' in location.lower()

                jobs.append({
                    'title': title,
                    'department': department,
                    'location': location,
                    'posting_date': '',
                    'remote': 'Yes' if is_remote else 'No',
                    'region': self._extract_region(location),
                    'url': url
                })

            except Exception as e:
                self.log(f"Error parsing card: {e}", level="WARNING")
                continue

        self.log(f"Completed: {len(jobs)} unique jobs scraped")
        return jobs

    def _extract_from_links(self, job_links):
        """Extract jobs from link elements when cards aren't found."""
        jobs = []
        seen_urls = set()

        # Get page text for location extraction
        body_text = self.driver.find_element(By.TAG_NAME, 'body').text

        for link in job_links:
            try:
                url = link.get_attribute('href')
                title = link.text.strip()

                # Skip invalid links
                if not url or not title:
                    continue
                if title.lower() in ['read more', 'apply', 'apply now']:
                    continue
                if url in seen_urls:
                    continue

                seen_urls.add(url)

                # Try to find location near this job in body text
                location = self._find_location_for_job(title, body_text)

                is_remote = 'remote' in title.lower() or 'remote' in location.lower()

                jobs.append({
                    'title': title,
                    'department': '',
                    'location': location,
                    'posting_date': '',
                    'remote': 'Yes' if is_remote else 'No',
                    'region': self._extract_region(location),
                    'url': url
                })

            except Exception as e:
                continue

        return jobs

    def _extract_location_from_text(self, text):
        """Extract location from card text."""
        lines = text.split('\n')

        # Common location patterns
        location_patterns = [
            r'([A-Za-z\s]+,\s*[A-Z]{2},?\s*USA)',  # City, ST, USA
            r'([A-Za-z\s]+,\s*[A-Z]{2})',  # City, ST
            r'(Remote)',
            r'([A-Za-z\s]+,\s*[A-Za-z\s]+,\s*[A-Za-z]+)',  # City, State, Country
        ]

        for line in lines:
            line = line.strip()
            # Skip obvious non-location lines
            if not line or len(line) > 100:
                continue
            if line.lower() in ['read more', 'apply', 'apply now']:
                continue

            # Check for location patterns
            for pattern in location_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    return match.group(1).strip()

            # Check for common location indicators
            if any(ind in line for ind in [', USA', ', US', ', Canada', ', UK', 'Remote']):
                return line

            # Check for state abbreviations
            if re.search(r',\s*[A-Z]{2}$', line):
                return line

        return ''

    def _find_location_for_job(self, title, body_text):
        """Find location for a specific job title in body text."""
        lines = body_text.split('\n')

        for i, line in enumerate(lines):
            if title in line:
                # Look at next few lines for location
                for j in range(i + 1, min(i + 5, len(lines))):
                    loc_line = lines[j].strip()
                    # Check if this looks like a location
                    if re.search(r',\s*[A-Z]{2}', loc_line) or 'Remote' in loc_line:
                        return loc_line
                    if any(ind in loc_line for ind in [', USA', ', US', ', Canada']):
                        return loc_line
                break

        return ''

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
            if 'United States' in location or 'USA' in location or 'US' in location:
                return 'United States'
            elif 'Canada' in location:
                return 'Canada'
            else:
                return 'Remote'

        if 'USA' in location or ', US' in location:
            return 'United States'
        if 'Canada' in location:
            return 'Canada'
        if 'UK' in location or 'United Kingdom' in location:
            return 'United Kingdom'

        # Extract last part (usually country)
        parts = location.split(',')
        if parts:
            return parts[-1].strip()

        return location
