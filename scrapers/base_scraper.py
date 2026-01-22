"""
Base Scraper Framework

Provides common functionality for all company scrapers.
"""

import requests
import csv
import json
from datetime import datetime
from pathlib import Path
from abc import ABC, abstractmethod


class BaseScraper(ABC):
    """Base class for all company scrapers."""

    def __init__(self, company_config):
        """
        Initialize the scraper with company configuration.

        Args:
            company_config (dict): Company configuration from companies_config.json
        """
        self.name = company_config['name']
        self.slug = company_config['slug']
        self.url = company_config['url']
        self.platform = company_config.get('platform', 'custom')
        self.config = company_config

        # Set up output directory
        self.output_dir = Path('companies') / self.slug
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def scrape(self):
        """
        Scrape jobs from the company website.

        Returns:
            list: List of job dictionaries with standardized format:
                {
                    'title': str,
                    'department': str,
                    'location': str,
                    'posting_date': str,
                    'remote': str ('Yes' or 'No'),
                    'region': str,
                    'url': str (optional)
                }
        """
        pass

    def save_to_csv(self, jobs, suffix=''):
        """
        Save jobs to CSV file.

        Args:
            jobs (list): List of job dictionaries
            suffix (str): Optional suffix for filename (e.g., 'new', 'consolidated')

        Returns:
            str: Path to the created file
        """
        if not jobs:
            return None

        today = datetime.now().strftime('%Y-%m-%d')
        filename = f"{self.slug}_jobs_{today}{suffix}.csv"
        filepath = self.output_dir / filename

        fieldnames = ['title', 'department', 'location', 'posting_date', 'remote', 'region', 'url']

        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(jobs)

        return str(filepath)

    def make_request(self, url, method='GET', **kwargs):
        """
        Make HTTP request with error handling.

        Args:
            url (str): URL to request
            method (str): HTTP method
            **kwargs: Additional arguments for requests

        Returns:
            requests.Response or None: Response object or None if failed
        """
        try:
            kwargs.setdefault('timeout', 30)
            kwargs.setdefault('headers', {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })

            if method.upper() == 'GET':
                response = requests.get(url, **kwargs)
            elif method.upper() == 'POST':
                response = requests.post(url, **kwargs)
            else:
                raise ValueError(f"Unsupported method: {method}")

            response.raise_for_status()
            return response

        except requests.exceptions.RequestException as e:
            print(f"  Error fetching {url}: {e}")
            return None

    def log(self, message, level='INFO'):
        """
        Log a message.

        Args:
            message (str): Message to log
            level (str): Log level (INFO, WARNING, ERROR)
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] [{level}] [{self.name}] {message}")

    def get_history_file(self):
        """Get path to job count history file."""
        return self.output_dir / 'job_count_history.csv'

    def get_tracking_file(self):
        """Get path to jobs tracking database file."""
        return self.output_dir / 'jobs_tracking.json'
