# Multi-Company Job Scraper

Automated system for scraping job postings from 32+ software companies simultaneously.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the scraper
python scrape_all_companies.py
```

Results are saved to `companies/<company_name>/` folders with timestamped CSV files.

## Project Structure

```
.
├── scrape_all_companies.py      # Main entry point - scrapes all companies
├── run_daily_automation.py      # Automated daily scraping with tracking
├── companies_config.json        # Company configurations (enable/disable)
├── requirements.txt             # Python dependencies
│
├── scrapers/                    # Scraper modules by platform
│   ├── base_scraper.py          # Base class
│   ├── workday_scraper.py       # Workday platform
│   ├── greenhouse_scraper.py    # Greenhouse ATS
│   ├── lever_scraper.py         # Lever ATS
│   └── ...                      # Other platform-specific scrapers
│
├── companies/                   # Output: job data by company
│   ├── veeva/
│   ├── workday/
│   ├── salesforce/
│   └── ...
│
├── output/                      # Scraping summaries and logs
├── logs/                        # Runtime logs
├── docs/                        # Documentation
└── archive/                     # Legacy single-company scraper
```

## Configuration

Edit `companies_config.json` to enable/disable companies:

```json
{
  "name": "Veeva",
  "slug": "veeva",
  "enabled": true
}
```

## Daily Automation

For automated daily scraping with job tracking:

```bash
python run_daily_automation.py
```

Or use the batch file on Windows:
```bash
run_daily_automation.bat
```

## Utilities

| Script | Purpose |
|--------|---------|
| `consolidate_jobs.py` | Merge job data across dates |
| `track_new_jobs.py` | Detect newly posted jobs |
| `track_job_counts.py` | Track job count trends |

## Documentation

See `docs/` for detailed guides:
- `MULTI_COMPANY_README.md` - Full usage guide
- `AUTOMATION_SETUP.md` - Automation configuration
- `DAILY_AUTOMATION_GUIDE.md` - Daily workflow
- `IMPLEMENTATION_SUMMARY.md` - Technical details

## Supported Platforms

- **Workday** - 10+ companies (API-based, reliable)
- **Greenhouse** - Multiple companies
- **Lever** - Multiple companies
- **Custom scrapers** - Veeva, Procore, ServiceTitan, etc.
