# Multi-Company Job Scraper

Automated system for scraping job postings from 32 software companies simultaneously.

## Quick Start

```bash
# Scrape all enabled companies
python scrape_all_companies.py
```

That's it! The system will scrape all enabled companies and save results to individual company folders.

## What Gets Created

### Folder Structure
```
companies/
├── veeva/
│   └── veeva_jobs_2026-01-03.csv
├── workday/
│   └── workday_jobs_2026-01-03.csv
├── alkami/
│   └── alkami_jobs_2026-01-03.csv
└── ... (32 companies total)

scraping_summary_2026-01-03.json  (overall results)
```

### CSV Format
Each company's CSV contains:
- `title` - Job title
- `department` - Department/team
- `location` - City, State/Country
- `posting_date` - When posted
- `remote` - Yes/No
- `region` - Geographic region
- `url` - Direct link to job posting (when available)

## Supported Companies

### ✅ Fully Supported (11 companies)
These use **Workday platform** - scraping works reliably via their API:
1. Workday
2. Autodesk
3. Alkami
4. nCino
5. Manhattan Associates
6. SPS Commerce
7. Vertex
8. Q2
9. CCC Intelligent Solutions
10. Workiva

### ✅ Custom Scraper
11. **Veeva** - Custom scraper (fully working)

### ⚠️ Best Effort (21 companies)
These use various platforms - success depends on site structure:
- HubSpot, Salesforce, ServiceNow, Shopify, Bill.com
- Procore, Toast, Guidewire, BlackLine
- Bentley, Nemetschek, Dassault 3DS
- Kinaxis, Ensono, Descartes
- AppFolio, Certara, Simulations Plus, Altus Group
- Tyler Technologies, Axon

**Note:** Sites that load jobs via JavaScript or use third-party platforms (like RippleMatch) may not return results with the generic scraper.

## Configuration

Edit `companies_config.json` to:
- Enable/disable companies: `"enabled": true/false`
- Add new companies
- Customize scraper settings

Example:
```json
{
  "name": "Veeva",
  "slug": "veeva",
  "url": "https://careers.veeva.com/job-search-results/",
  "platform": "custom",
  "scraper": "veeva_scraper",
  "enabled": true
}
```

## Advanced Usage

### Disable Specific Companies

```python
# Edit companies_config.json and set:
"enabled": false
```

### Scrape Single Company

```python
from scrapers.veeva_scraper import VeevaScraper
import json

with open('companies_config.json') as f:
    companies = json.load(f)['companies']

veeva_config = next(c for c in companies if c['slug'] == 'veeva')
scraper = VeevaScraper(veeva_config)
jobs = scraper.scrape()
scraper.save_to_csv(jobs)
```

### Adjust Request Delay

In `scrape_all_companies.py`, modify:
```python
result = scrape_company(company, delay=2)  # 2 seconds between companies
```

## Understanding Results

### Summary Report
`scraping_summary_YYYY-MM-DD.json` contains:
- Total companies scraped
- Success/failure counts
- Total jobs found
- Detailed results per company

Example:
```json
{
  "date": "2026-01-03",
  "total_companies": 32,
  "successful": 15,
  "failed": 17,
  "total_jobs": 2450,
  "results": [...]
}
```

### Why Some Companies Fail

**Common reasons:**
1. **JavaScript-heavy sites** - Jobs load after page render (not accessible via simple HTTP)
2. **Third-party platforms** - Redirect to external job boards
3. **Rate limiting** - Too many requests blocked
4. **Site structure changes** - Company updated their careers page

## Integrating with Existing System

### Add Tracking & Consolidation

The existing tools (track_new_jobs.py, consolidate_jobs.py, track_job_counts.py) work with the multi-company system!

For each company:
```bash
cd companies/veeva
python ../../track_new_jobs.py  # (needs adaptation)
python ../../consolidate_jobs.py
python ../../track_job_counts.py
```

### Daily Automation

Create a master daily script that:
1. Runs `scrape_all_companies.py`
2. For each successful company:
   - Detect new jobs
   - Create consolidated view
   - Track job counts

## Customizing Scrapers

### Add a New Company

1. Add to `companies_config.json`:
```json
{
  "name": "New Company",
  "slug": "newcompany",
  "url": "https://newcompany.com/careers",
  "platform": "custom",
  "scraper": "generic_scraper",
  "enabled": true
}
```

2. Test: `python scrape_all_companies.py`

3. If generic scraper doesn't work, create custom scraper in `scrapers/`:

```python
from scrapers.base_scraper import BaseScraper

class NewCompanyScraper(BaseScraper):
    def scrape(self):
        # Custom scraping logic
        jobs = []
        # ... extract jobs ...
        return jobs
```

### Platform-Specific Scrapers

**Workday** - `scrapers/workday_scraper.py`
- Uses their JSON API
- Automatically handles pagination
- Works for all *.myworkdayjobs.com sites

**Generic** - `scrapers/generic_scraper.py`
- Tries JSON-LD structured data
- Tries Greenhouse ATS pattern
- Tries Lever ATS pattern
- Tries generic JSON patterns

**Custom** - Create your own in `scrapers/`

## Performance

**Tested performance:**
- 3 companies: ~13 seconds (1,017 jobs)
- Expected for 32 companies: ~2-3 minutes
- Includes 2-second delay between companies (respectful to servers)

## Troubleshooting

### "No jobs found" for a company

1. Check if site loads jobs via JavaScript:
   - Visit the URL in a browser
   - View page source (Ctrl+U)
   - Search for job titles - if not found, jobs are loaded dynamically

2. Try manually:
```python
import requests
r = requests.get('company_url')
print('job' in r.text.lower())  # Should be True if accessible
```

3. Consider these solutions:
   - Use Selenium/Playwright for JavaScript sites
   - Find their API endpoint (Chrome DevTools Network tab)
   - Use third-party job aggregators

### Company's site structure changed

Update the scraper in `scrapers/` directory or use generic scraper with different patterns.

### Rate limiting / 429 errors

Increase delay between requests:
```python
result = scrape_company(company, delay=5)  # 5 seconds
```

## Best Practices

1. **Run during off-peak hours** - Less likely to hit rate limits
2. **Monitor success rates** - Check summary reports
3. **Update regularly** - Sites change, scrapers need maintenance
4. **Respect robots.txt** - Be a good web citizen
5. **Cache results** - Don't re-scrape unnecessarily

## Next Steps

Consider enhancing with:
- Email notifications when new jobs appear
- Filtering by keywords/departments
- Salary data extraction (when available)
- Application tracking
- Database storage instead of CSV
- Web dashboard for viewing results

## Support

The generic scraper works best for sites with:
- Jobs in initial HTML
- JSON-LD structured data
- Common ATS platforms (Greenhouse, Lever)

For companies using heavy JavaScript or third-party platforms, custom scrapers may be needed.
