# Job Postings Scraper - Project Context

## Overview
Automated job scraper that tracks job postings across multiple companies in the enterprise software / proptech / supply chain space. Runs daily via GitHub Actions.

## Repository
- GitHub: https://github.com/hlsansome-web/job-postings.git
- Branch: main

## Architecture

### Core Files
- `scrape_all_companies.py` - Main entry point, orchestrates all scrapers
- `companies_config.json` - Company configurations (URLs, scraper types, enabled status)
- `scrapers/` - Scraper implementations by platform type
- `companies/` - Output directory with CSV files per company

### Scraper Types
| Scraper | Platform | File |
|---------|----------|------|
| `workday_scraper` | Workday job boards | `workday_scraper.py` |
| `lever_scraper` | Lever ATS | `lever_scraper.py` |
| `greenhouse_scraper` | Greenhouse ATS | `greenhouse_scraper.py` |
| `ashby_scraper` | Ashby ATS (API-based) | `ashby_scraper.py` |
| `icims_scraper` | iCIMS ATS | `icims_scraper.py` |
| `gem_scraper` | Gem platform (headless) | `gem_scraper.py` |
| `successfactors_scraper` | SAP SuccessFactors | `successfactors_scraper.py` |
| `tyler_scraper` | Tyler Technologies (custom) | `tyler_scraper.py` |
| `dassault_scraper` | Dassault 3DS (Vue.js) | `dassault_scraper.py` |
| `yardi_scraper` | Yardi careers | `yardi_scraper.py` |
| `simulationsplus_scraper` | Simulations Plus (disabled) | `simulationsplus_scraper.py` |

### Adding a New Scraper
1. Create `scrapers/new_scraper.py` extending `BaseScraper` or `HeadlessScraper`
2. Add import to `scrapers/__init__.py`
3. Add import and mapping to `scrape_all_companies.py`
4. Add company entry to `companies_config.json`

## Companies Tracked (as of 2026-01-22)

### Using Custom Scrapers (built this session)
| Company | Slug | Scraper | Notes |
|---------|------|---------|-------|
| Descartes | `descartes` | `successfactors_scraper` | SAP SuccessFactors |
| Tyler Technologies | `tyler` | `tyler_scraper` | Anti-detection needed |
| Dassault Systemes | `3ds` | `dassault_scraper` | Vue.js dynamic site |
| Yardi | `yardi` | `yardi_scraper` | Anti-detection needed |
| Simulations Plus | `simulationsplus` | `simulationsplus_scraper` | DISABLED - no public job board |

### Using Existing Scrapers (added this session)
| Company | Slug | Scraper |
|---------|------|---------|
| o9 Solutions | `o9solutions` | `workday_scraper` |
| Blue Yonder | `blueyonder` | `workday_scraper` |
| Manhattan Associates | `manhattan` | `workday_scraper` |
| Lumin Digital | `lumindigital` | `lever_scraper` |
| Entrata | `entrata` | `lever_scraper` |
| Blend | `blend` | `greenhouse_scraper` |
| Parloa | `parloa` | `greenhouse_scraper` |
| RealPage | `realpage` | `icims_scraper` |
| EliseAI | `eliseai` | `ashby_scraper` |
| Sierra AI | `sierra` | `ashby_scraper` |
| Decagon AI | `decagon` | `ashby_scraper` |
| Serval | `serval` | `ashby_scraper` |
| Bilt Rewards | `bilt` | `gem_scraper` |

## Technical Notes

### Anti-Detection for Headless Browsers
Some sites (Tyler, Yardi) block headless browsers. Solution in `_setup_driver()`:
```python
chrome_options.add_argument('--disable-blink-features=AutomationControlled')
chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
chrome_options.add_experimental_option('useAutomationExtension', False)
# After driver creation:
self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
    'source': "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
})
```

### Gem Scraper URL Pattern Fix
The Gem scraper needed to handle company-specific URL patterns like `/bilt/job-id` not just `/jobs/`:
```python
company_slug = url.rstrip('/').split('/')[-1]
if '/jobs/' not in job_url and f'/{company_slug}/' not in job_url:
    continue
```

### Known Issues / Failed Scrapers
These companies use `generic_scraper` but don't work properly:
- Altus Group
- Appfolio
- Buildium
- Guidewire
- Procore
- Rent Manager
- ResMan
- RPTA
- Sage Intacct

### Companies Never Added (discussed but not implemented)
- ADP - complex career site
- Medidata - needs investigation

## Automation

### GitHub Actions
- Workflow: `.github/workflows/daily-scrape.yml`
- Schedule: Runs daily
- Triggers scrape for all enabled companies

### Running Manually
```bash
# All companies
python scrape_all_companies.py

# Specific company
python scrape_all_companies.py --company descartes
python scrape_all_companies.py --company yardi
```

## Output Format
CSV files in `companies/{slug}/{slug}_jobs_{date}.csv`:
```
title,department,location,posting_date,remote,region,url
```

## Future Ideas Discussed

### Track Filled Positions
Options for tracking who fills positions:
1. **Removal tracking** - Diff scrapes to detect when postings disappear
2. **LinkedIn monitoring** - Manual search for new hires when posting closes
3. **Third-party APIs** - People Data Labs, Apollo.io, ZoomInfo, LinkedIn Sales Navigator

Could add to scraper:
- `filled_positions.csv` - Log removed postings with date
- Days-open tracking per position
- Alert when senior positions filled

## Session Summary (2026-01-22)

### Created
- 5 new scraper files (successfactors, tyler, dassault, yardi, simulationsplus)
- Added 16 new companies to tracking
- Fixed Gem scraper URL pattern bug

### Commits
1. `572f8ce` - Add scrapers for Descartes, Tyler, Dassault, Simulations Plus, and Yardi
2. `3d0802f` - Fix Gem scraper to handle company-specific URL patterns
3. `cea2406` - Add job data for 16 companies (2026-01-22 scrape)

### Job Counts (2026-01-22)
| Company | Jobs |
|---------|------|
| Yardi | 55 |
| RealPage | 47 |
| Blue Yonder | 40 |
| Parloa | 39 |
| Manhattan | 38 |
| Entrata | 33 |
| Dassault (3DS) | 25 |
| o9 Solutions | 23 |
| Descartes | 21 |
| Tyler | 17 |
| Serval | 16 |
| Blend | 13 |
| EliseAI | 11 |
| Lumin Digital | 9 |
| Sierra | 8 |
| Bilt | 7 |
| Decagon | 60 |
