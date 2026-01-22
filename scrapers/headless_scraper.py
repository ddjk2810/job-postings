"""
Headless Browser Base Scraper

Base class for scrapers that require JavaScript rendering.
Uses Selenium with Chrome in headless mode.
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from scrapers.base_scraper import BaseScraper
import time


class HeadlessScraper(BaseScraper):
    """Base class for scrapers requiring headless browser."""

    def __init__(self, company_config):
        """
        Initialize headless scraper.

        Args:
            company_config (dict): Company configuration
        """
        super().__init__(company_config)
        self.driver = None

    def _setup_driver(self):
        """Set up Chrome driver in headless mode."""
        if self.driver:
            return

        self.log("Setting up headless Chrome browser...")

        chrome_options = Options()
        chrome_options.add_argument('--headless=new')  # New headless mode
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')

        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.log("Browser ready")
        except Exception as e:
            self.log(f"Failed to setup browser: {e}", "ERROR")
            raise

    def _close_driver(self):
        """Close the browser."""
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
                self.log("Browser closed")
            except Exception as e:
                self.log(f"Error closing browser: {e}", "WARNING")

    def wait_for_element(self, by, value, timeout=10):
        """
        Wait for an element to be present.

        Args:
            by: Selenium By locator type
            value: Locator value
            timeout: Maximum wait time in seconds

        Returns:
            WebElement or None
        """
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            self.log(f"Timeout waiting for element: {value}", "WARNING")
            return None

    def wait_for_elements(self, by, value, timeout=10):
        """
        Wait for elements to be present.

        Args:
            by: Selenium By locator type
            value: Locator value
            timeout: Maximum wait time in seconds

        Returns:
            List of WebElements or empty list
        """
        try:
            elements = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_all_elements_located((by, value))
            )
            return elements
        except TimeoutException:
            self.log(f"Timeout waiting for elements: {value}", "WARNING")
            return []

    def scrape(self):
        """
        Main scraping method - to be overridden by subclasses.

        Returns:
            list: List of job dictionaries
        """
        try:
            self._setup_driver()
            jobs = self._scrape_jobs()
            return jobs
        except Exception as e:
            self.log(f"Error during scraping: {e}", "ERROR")
            return []
        finally:
            self._close_driver()

    def _scrape_jobs(self):
        """
        Internal method to scrape jobs - MUST be implemented by subclasses.

        Returns:
            list: List of job dictionaries
        """
        raise NotImplementedError("Subclasses must implement _scrape_jobs()")
