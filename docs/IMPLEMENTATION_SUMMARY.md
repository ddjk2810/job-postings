# Multi-Company Job Scraper - Implementation Summary

## What Was Built

A complete automated system for scraping job postings from 32 software companies simultaneously.

---

## 📊 Current Status

### Working Companies: **12 of 32** (37.5%)

**Total Jobs Scraped:** ~1,322 jobs

| Company | Platform | Jobs | Status |
|---------|----------|------|--------|
| Veeva | Custom | 945 | ✅ Working |
| Workday | Workday API | 40 | ✅ Working |
| Autodesk | Workday API | 40 | ✅ Working |
| Q2 | Workday API | 40 | ✅ Working |
| Workiva | Workday API | 40 | ✅ Working |
| nCino | Workday API | 36 | ✅ Working |
| SPS Commerce | Workday API | 35 | ✅ Working |
| Alkami | Workday API | 32 | ✅ Working |
| Manhattan Associates | Workday API | 30 | ✅ Working |
| CCC Intelligent Solutions | Workday API | 20 | ✅ Working |
| Vertex | Workday API | 18 | ✅ Working |
| **Bill.com** | **Greenhouse API** | **46** | **✅ NEW!** |

---

## 🛠️ Scraper Architecture

### Platform-Based Scrapers (Reusable)

Built 5 specialized scrapers that work across multiple companies:

1. **Workday Scraper** (`workday_scraper.py`)
   - Works for 10 companies
   - Uses Workday's JSON API
   - Automatic pagination
   - **Companies:** Workday, Autodesk, Alkami, nCino, Manhattan, SPS Commerce, Vertex, Q2, CCC, Workiva

2. **Veeva Scraper** (`veeva_scraper.py`)
   - Custom implementation for Veeva
   - Extracts JavaScript variable with job data
   - **Companies:** Veeva

3. **Greenhouse Scraper** (`greenhouse_scraper.py`) 🆕
   - Works for Greenhouse ATS platform
   - Uses public JSON API
   - **Companies:** Bill.com

4. **Lever Scraper** (`lever_scraper.py`) 🆕
   - Works for Lever ATS platform
   - Ready to use when we find Lever-based companies
   - **Companies:** (None identified yet)

5. **Generic Scraper** (`generic_scraper.py`)
   - Fallback for unknown platforms
   - Tries multiple patterns (JSON-LD, Greenhouse, Lever, generic JSON)
   - Success rate varies by site

---

## 📁 System Architecture

```
my-new-project/
├── scrapers/
│   ├── base_scraper.py           # Base class with common functionality
│   ├── veeva_scraper.py          # Veeva custom scraper
│   ├── workday_scraper.py        # Workday platform (10 companies)
│   ├── greenhouse_scraper.py     # Greenhouse platform (1+ companies) 🆕
│   ├── lever_scraper.py          # Lever platform (ready to use) 🆕
│   └── generic_scraper.py        # Fallback scraper
│
├── companies/                     # Output directory
│   ├── veeva/
│   │   └── veeva_jobs_2026-01-03.csv
│   ├── bill/
│   │   └── bill_jobs_2026-01-03.csv
│   └── ... (one folder per company)
│
├── scrape_all_companies.py       # Main runner script
├── companies_config.json          # Company configurations
├── scraping_summary_YYYY-MM-DD.json  # Detailed results
│
└── Documentation/
    ├── MULTI_COMPANY_README.md
    ├── FAILED_COMPANIES_ANALYSIS.md  🆕
    └── IMPLEMENTATION_SUMMARY.md     🆕
```

---

## 🚀 How to Use

### Run All Companies
```bash
python scrape_all_companies.py
```

### Results
- Individual CSV files in `companies/[company_name]/`
- Summary report: `scraping_summary_YYYY-MM-DD.json`
- Each company gets its own folder with dated CSV files

### CSV Format
```csv
title,department,location,posting_date,remote,region,url
Senior Software Engineer,Engineering,"Boston, MA",2026-01-03,No,United States,https://...
```

---

## 📈 Success Breakdown

### Platform Distribution (Working Companies)

- **Workday Platform:** 10 companies (83% of working)
- **Custom Scrapers:** 2 companies (Veeva, Bill.com)

### Why Others Failed

**20 remaining failed companies fall into 3 categories:**

1. **JavaScript-Heavy (14 companies)** - Need headless browser
   - Procore, Shopify, Toast, Guidewire, BlackLine, AppFolio, Certara
   - Simulations Plus, Altus Group, Tyler Tech, Bentley, Nemetschek
   - Dassault 3DS, Descartes

2. **Third-Party Platforms (1 company)**
   - HubSpot (uses RippleMatch redirect)

3. **Bot Protection (3 companies)**
   - ServiceNow (403 Forbidden)
   - Salesforce (400 error)
   - Axon (SSL certificate issues)

4. **Need Platform Research (2 companies)**
   - Kinaxis (iCIMS platform)
   - Ensono (UltiPro platform)

See `FAILED_COMPANIES_ANALYSIS.md` for detailed breakdown.

---

## 🔧 Technical Features

### Modular Design
- Base scraper class with common functionality
- Easy to add new platform scrapers
- Configuration-driven (JSON file)

### Error Handling
- Graceful failures (one company failing doesn't stop others)
- Detailed logging with timestamps
- Summary report shows successes and failures

### Rate Limiting
- 2-second delay between companies (respectful to servers)
- Configurable timeouts
- Proper User-Agent headers

### Data Quality
- Standardized CSV format across all companies
- Location, department, remote status extraction
- Direct links to job postings (when available)

---

## 💡 What You Can Do Now

### Immediate Use
```bash
# Scrape all 12 working companies (~1,300+ jobs)
python scrape_all_companies.py

# Results in ~1-2 minutes
```

### Integration with Existing Tools
Your existing Veeva tools can be adapted:
- `track_new_jobs.py` - Detect new postings
- `consolidate_jobs.py` - Merge duplicate titles
- `track_job_counts.py` - Track historical trends

### Daily Automation
- Set up Windows Task Scheduler
- Run daily to get fresh job data
- Track trends across all companies

---

## 🎯 Next Steps (Optional)

### Phase 1: Low Effort Improvements

1. **Research Platform IDs** for companies using:
   - iCIMS (Kinaxis)
   - UltiPro (Ensono)

2. **Build Platform Scrapers:**
   - `icims_scraper.py`
   - `ultipro_scraper.py`

### Phase 2: Medium Effort (If Needed)

3. **Headless Browser Implementation**
   - Install Selenium or Playwright
   - Create `headless_scraper.py` base class
   - Implement for high-priority companies only

### Phase 3: Skip These

- HubSpot (third-party redirect, not worth it)
- Companies with aggressive bot protection
- Low-priority JavaScript-heavy sites

---

## 📊 ROI Assessment

### Current Achievement
- **37.5% success rate** (12/32 companies)
- **1,322+ jobs** captured
- **Fully automated** system
- **Platform-based** approach (scalable)

### Time Invested
- ~2 hours to build entire system
- Reusable scrapers for future companies
- Documentation for maintenance

### Maintenance
- Workday/Greenhouse APIs are stable
- Low maintenance for working scrapers
- Easy to disable broken scrapers

---

## 🔍 Key Insights

1. **Platform consolidation is real**
   - 10 companies use Workday
   - Greenhouse/Lever are common
   - Building platform scrapers >>> custom scrapers

2. **JavaScript rendering is the main challenge**
   - 70% of failures due to JS-heavy sites
   - Headless browsers solve this but add complexity

3. **Third-party redirects are not worth pursuing**
   - Companies like HubSpot outsource recruiting
   - Scraping third-party platforms is fragile

4. **APIs are the gold standard**
   - Workday: Clean JSON API
   - Greenhouse: Public API
   - Much more reliable than HTML parsing

---

## 📝 Files Created

### Core System
- `scrapers/base_scraper.py` - Base class
- `scrapers/veeva_scraper.py` - Veeva custom
- `scrapers/workday_scraper.py` - Workday platform
- `scrapers/greenhouse_scraper.py` - Greenhouse platform 🆕
- `scrapers/lever_scraper.py` - Lever platform 🆕
- `scrapers/generic_scraper.py` - Fallback
- `scrape_all_companies.py` - Main runner
- `companies_config.json` - Configuration

### Documentation
- `MULTI_COMPANY_README.md` - User guide
- `FAILED_COMPANIES_ANALYSIS.md` - Detailed failure analysis 🆕
- `IMPLEMENTATION_SUMMARY.md` - This file 🆕

### Output Examples
- `companies/*/company_jobs_YYYY-MM-DD.csv` - Job listings
- `scraping_summary_YYYY-MM-DD.json` - Run results

---

## 🎉 Success Metrics

✅ **12 companies scraping successfully**
✅ **1,322+ jobs captured**
✅ **5 platform scrapers built**
✅ **Fully automated workflow**
✅ **Comprehensive documentation**
✅ **Scalable architecture**
✅ **~2 minute runtime**

---

## Questions?

- See `MULTI_COMPANY_README.md` for usage details
- See `FAILED_COMPANIES_ANALYSIS.md` for failed companies analysis
- Check `scraping_summary_YYYY-MM-DD.json` for detailed results
