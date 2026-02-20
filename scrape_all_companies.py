#!/usr/bin/env python3
"""
Multi-Company Job Scraper

Master script that scrapes job postings from multiple companies.
"""

import argparse
import json
import time
from datetime import datetime
from pathlib import Path
from collections import defaultdict

from scrapers.veeva_scraper import VeevaScraper
from scrapers.workday_scraper import WorkdayScraper
from scrapers.greenhouse_scraper import GreenhouseScraper
from scrapers.lever_scraper import LeverScraper
from scrapers.procore_scraper import ProcoreScraper
from scrapers.appfolio_scraper import AppFolioScraper
from scrapers.certara_scraper import CertaraScraper
from scrapers.kinaxis_scraper import KinaxisScraper
from scrapers.servicetitan_scraper import ServiceTitanScraper
from scrapers.dayforce_scraper import DayforceScraper
from scrapers.toast_scraper import ToastScraper
from scrapers.generic_scraper import GenericScraper
from scrapers.ashby_scraper import AshbyScraper
from scrapers.gem_scraper import GemScraper
from scrapers.successfactors_scraper import SuccessFactorsScraper
from scrapers.tyler_scraper import TylerScraper
from scrapers.simulationsplus_scraper import SimulationsPlusScraper
from scrapers.dassault_scraper import DassaultScraper
from scrapers.yardi_scraper import YardiScraper
from scrapers.teamtailor_scraper import TeamtailorScraper
from scrapers.ultipro_scraper import UltiProScraper
from scrapers.workable_scraper import WorkableScraper
from scrapers.oracle_hcm_scraper import OracleHCMScraper
from scrapers.adp_scraper import ADPScraper
from scrapers.static_html_scraper import StaticHTMLScraper


def load_companies_config(config_file='companies_config.json', fund=None):
    """
    Load companies configuration from JSON file.

    Args:
        config_file (str): Path to configuration file
        fund (str): Optional fund filter ('partners' or 'scf')

    Returns:
        list: List of company configurations
    """
    with open(config_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    companies = data['companies']
    if fund:
        companies = [c for c in companies if c.get('fund') == fund]
    return companies


def get_scraper_class(scraper_name):
    """
    Get the appropriate scraper class based on name.

    Args:
        scraper_name (str): Name of the scraper

    Returns:
        class: Scraper class
    """
    scrapers = {
        'veeva_scraper': VeevaScraper,
        'workday_scraper': WorkdayScraper,
        'greenhouse_scraper': GreenhouseScraper,
        'lever_scraper': LeverScraper,
        'procore_scraper': ProcoreScraper,
        'appfolio_scraper': AppFolioScraper,
        'certara_scraper': CertaraScraper,
        'kinaxis_scraper': KinaxisScraper,
        'servicetitan_scraper': ServiceTitanScraper,
        'dayforce_scraper': DayforceScraper,
        'toast_scraper': ToastScraper,
        'generic_scraper': GenericScraper,
        'ashby_scraper': AshbyScraper,
        'gem_scraper': GemScraper,
        'successfactors_scraper': SuccessFactorsScraper,
        'tyler_scraper': TylerScraper,
        'simulationsplus_scraper': SimulationsPlusScraper,
        'dassault_scraper': DassaultScraper,
        'yardi_scraper': YardiScraper,
        'teamtailor_scraper': TeamtailorScraper,
        'ultipro_scraper': UltiProScraper,
        'workable_scraper': WorkableScraper,
        'oracle_hcm_scraper': OracleHCMScraper,
        'adp_scraper': ADPScraper,
        'static_html_scraper': StaticHTMLScraper,
    }
    return scrapers.get(scraper_name, GenericScraper)


def scrape_company(company_config, delay=2):
    """
    Scrape jobs for a single company.

    Args:
        company_config (dict): Company configuration
        delay (int): Delay in seconds between requests

    Returns:
        dict: Results dictionary with jobs and metadata
    """
    name = company_config['name']
    slug = company_config['slug']

    print(f"\n{'='*60}")
    print(f"Scraping: {name}")
    print(f"{'='*60}")

    # Add delay to be respectful to servers
    if delay > 0:
        time.sleep(delay)

    try:
        # Get appropriate scraper
        scraper_class = get_scraper_class(company_config['scraper'])
        scraper = scraper_class(company_config)

        # Scrape jobs
        jobs = scraper.scrape()

        # Save to CSV
        if jobs:
            csv_path = scraper.save_to_csv(jobs)
            print(f"[OK] Saved {len(jobs)} jobs to {csv_path}")

            return {
                'success': True,
                'company': name,
                'slug': slug,
                'job_count': len(jobs),
                'csv_path': csv_path
            }
        else:
            print(f"[WARN] No jobs found for {name}")
            return {
                'success': False,
                'company': name,
                'slug': slug,
                'job_count': 0,
                'csv_path': None,
                'error': 'No jobs found'
            }

    except Exception as e:
        print(f"[ERROR] Error scraping {name}: {e}")
        return {
            'success': False,
            'company': name,
            'slug': slug,
            'job_count': 0,
            'csv_path': None,
            'error': str(e)
        }


def print_summary(results):
    """
    Print summary of scraping results.

    Args:
        results (list): List of result dictionaries
    """
    print("\n" + "="*60)
    print("SCRAPING SUMMARY")
    print("="*60)

    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]

    print(f"\nTotal companies: {len(results)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")

    if successful:
        total_jobs = sum(r['job_count'] for r in successful)
        print(f"\nTotal jobs scraped: {total_jobs}")

        print(f"\nTop companies by job count:")
        print("-" * 60)
        sorted_results = sorted(successful, key=lambda x: x['job_count'], reverse=True)
        for i, result in enumerate(sorted_results[:10], 1):
            print(f"{i:2d}. {result['company']}: {result['job_count']} jobs")

    if failed:
        print(f"\nFailed companies:")
        print("-" * 60)
        for result in failed:
            error = result.get('error', 'Unknown error')
            print(f"  [X] {result['company']}: {error}")

    print("="*60)


def save_summary_report(results, fund=None):
    """
    Save summary report to file.

    Args:
        results (list): List of result dictionaries
        fund (str): Optional fund name for filename suffix
    """
    today = datetime.now().strftime('%Y-%m-%d')
    suffix = f"_{fund}" if fund else ""
    report_file = f"scraping_summary_{today}{suffix}.json"

    report = {
        'date': today,
        'timestamp': datetime.now().isoformat(),
        'total_companies': len(results),
        'successful': len([r for r in results if r['success']]),
        'failed': len([r for r in results if not r['success']]),
        'total_jobs': sum(r['job_count'] for r in results if r['success']),
        'results': results
    }

    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    print(f"\nDetailed report saved to: {report_file}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Multi-Company Job Scraper')
    parser.add_argument('--fund', choices=['partners', 'scf'],
                        help='Filter companies by fund (partners or scf)')
    parser.add_argument('--company', type=str,
                        help='Scrape a single company by slug')
    args = parser.parse_args()

    start_time = datetime.now()

    fund_label = f" [{args.fund.upper()} Fund]" if args.fund else ""
    print("="*60)
    print(f"MULTI-COMPANY JOB SCRAPER{fund_label}")
    print("="*60)
    print(f"Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # Load configuration
    try:
        companies = load_companies_config(fund=args.fund)
    except FileNotFoundError:
        print("Error: companies_config.json not found")
        return
    except json.JSONDecodeError as e:
        print(f"Error parsing companies_config.json: {e}")
        return

    # Filter enabled companies
    enabled_companies = [c for c in companies if c.get('enabled', True)]

    # Filter by specific company if requested
    if args.company:
        enabled_companies = [c for c in enabled_companies if c['slug'] == args.company]
        if not enabled_companies:
            print(f"Error: Company '{args.company}' not found or not enabled")
            return

    print(f"\nFound {len(enabled_companies)} enabled companies")
    print("Starting scraping process...\n")

    # Scrape each company
    results = []
    for i, company in enumerate(enabled_companies, 1):
        print(f"\n[{i}/{len(enabled_companies)}]", end=" ")
        result = scrape_company(company, delay=2)
        results.append(result)

    # Print summary
    print_summary(results)

    # Save report
    save_summary_report(results, fund=args.fund)

    # Duration
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print(f"\nCompleted at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
