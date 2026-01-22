# Headless Scrapers Implementation Summary

## What Was Built

Successfully implemented headless browser scrapers for 4 companies using Selenium and Chrome.

---

## ✅ Working Headless Scrapers (3/4)

| Company | Jobs Found | Status | Notes |
|---------|-----------|--------|-------|
| **Procore** | 34 | ✅ Working | Construction management software |
| **AppFolio** | 2 | ✅ Working | Property management software |
| **Kinaxis** | 1 | ✅ Working | Supply chain planning (iCIMS platform) |

### Details

**Procore** - `procore_scraper.py`
- URL: careers.procore.com/jobs/search
- Platform: Rails/Turbo
- Jobs scraped: 34
- Runtime: ~10 seconds
- Status: ✅ **Fully working**

**AppFolio** - `appfolio_scraper.py`
- URL: www.appfolio.com/open-roles
- Platform: Custom
- Jobs scraped: 2
- Runtime: ~10 seconds
- Status: ✅ **Working** (low job count is accurate)

**Kinaxis** - `kinaxis_scraper.py`
- URL: careers-kinaxis.icims.com
- Platform: iCIMS
- Jobs scraped: 1
- Runtime: ~12 seconds
- Status: ✅ **Working** (low job count is accurate)

---

## ❌ Not Working (1/4)

| Company | Status | Issue | Next Steps |
|---------|--------|-------|-----------|
| **Certara** | ❌ Failed | Timeout finding job listings | Needs debugging |

### Certara Issue

**Problem:** Scraper times out waiting for job elements
- Tried multiple CSS selectors
- Jobs may be in iframe or different structure
- Needs manual inspection of page structure

**Options:**
1. Investigate page structure more carefully
2. Try different selectors
3. Check if jobs are in iframe
4. Consider skipping (low priority company)

---

## 📊 Updated Company Status

### Total Working: **15 companies** (was 12)
- Previous: 12 companies, 1,322 jobs
- **New: +3 companies, +37 jobs**
- **Total: 15 companies, ~1,359 jobs**

### Breakdown by Platform

| Platform | Companies | Jobs | Scraper |
|----------|-----------|------|---------|
| Workday API | 10 | ~331 | `workday_scraper.py` |
| Custom | 1 | 945 | `veeva_scraper.py` |
| Greenhouse API | 1 | 46 | `greenhouse_scraper.py` |
| **Headless Browser** | **3** | **37** | **New scrapers** |

---

## 🛠️ Technical Implementation

### Base Class: `headless_scraper.py`

Created a reusable base class for all headless browser operations:

```python
class HeadlessScraper(BaseScraper):
    - _setup_driver() - Initializes Chrome in headless mode
    - _close_driver() - Cleanup
    - wait_for_element() - Wait for single element
    - wait_for_elements() - Wait for multiple elements
    - scrape() - Main entry point
```

### Company-Specific Scrapers

Each company scraper extends `HeadlessScraper` and implements `_scrape_jobs()`:

1. **procore_scraper.py** - Procore careers
2. **appfolio_scraper.py** - AppFolio careers
3. **kinaxis_scraper.py** - Kinaxis iCIMS platform
4. **certara_scraper.py** - Certara (needs fixes)

### Dependencies Installed

```bash
pip install selenium webdriver-manager
```

- `selenium` - Browser automation
- `webdriver-manager` - Automatic ChromeDriver management

---

## ⚙️ How It Works

### Workflow

1. **Setup Browser**
   - Launches Chrome in headless mode
   - Configures options (no sandbox, disable GPU, etc.)
   - Sets user agent to avoid detection

2. **Load Page**
   - Navigates to company careers URL
   - Waits for JavaScript to render

3. **Find Job Elements**
   - Uses CSS selectors to find job listings
   - Tries multiple selector patterns
   - Waits up to 15 seconds for elements

4. **Extract Data**
   - Loops through each job element
   - Extracts title, URL, location (when available)
   - Handles exceptions gracefully

5. **Cleanup**
   - Closes browser
   - Returns job list

### Runtime

- **Per company:** ~10-15 seconds
- **Headless browsers are slower** than API calls
- But they can access any JavaScript-rendered site

---

## 📈 Performance Comparison

| Method | Speed | Reliability | Maintenance |
|--------|-------|-------------|-------------|
| **API-based** (Workday, Greenhouse) | ⚡ Fast (1-2 sec) | ✅ High | ⚪ Low |
| **HTML parsing** (Veeva) | ⚡ Fast (1-2 sec) | ✅ High | ⚪ Low |
| **Headless browser** (New) | 🐢 Slow (10-15 sec) | 🟡 Medium | 🟡 Medium |

**Trade-offs:**
- Headless is **slower** but **more flexible**
- Can scrape any JavaScript-heavy site
- Higher resource usage (runs actual browser)
- May break if site structure changes

---

## 🚀 Usage

### Run All Companies (Including New Ones)

```bash
python scrape_all_companies.py
```

Now includes the 3 new headless scrapers automatically.

### Run Just Headless Scrapers

```python
# Disable all except headless companies
# Edit companies_config.json or use script
```

### Output

Each company gets its own CSV:
- `companies/procore/procore_jobs_2026-01-03.csv`
- `companies/appfolio/appfolio_jobs_2026-01-03.csv`
- `companies/kinaxis/kinaxis_jobs_2026-01-03.csv`

---

## 🔧 Troubleshooting

### ChromeDriver Issues

If Chrome driver fails to install:
```bash
# Manually install ChromeDriver
# Or use different browser (Firefox)
```

### Timeout Errors

If elements don't load:
1. Increase timeout in `wait_for_elements(timeout=15)`
2. Try different CSS selectors
3. Check if page structure changed

### No Jobs Found

If scraper returns 0 jobs:
1. Check if page loaded correctly
2. Inspect page source for actual selectors
3. May need to adjust CSS selectors in scraper

---

## 📝 Files Created

### Scrapers
- `scrapers/headless_scraper.py` - Base class ✅
- `scrapers/procore_scraper.py` - Procore ✅
- `scrapers/appfolio_scraper.py` - AppFolio ✅
- `scrapers/kinaxis_scraper.py` - Kinaxis ✅
- `scrapers/certara_scraper.py` - Certara (needs fix) ⚠️

### Output
- `companies/procore/procore_jobs_2026-01-03.csv` - 34 jobs
- `companies/appfolio/appfolio_jobs_2026-01-03.csv` - 2 jobs
- `companies/kinaxis/kinaxis_jobs_2026-01-03.csv` - 1 job

### Documentation
- `HEADLESS_SCRAPERS_SUMMARY.md` - This file

---

## 🎯 Results Summary

### Before Headless Scrapers
- **12 companies** working
- **1,322 jobs**
- **32 total companies**
- **37.5% success rate**

### After Headless Scrapers
- **15 companies** working (+3)
- **~1,359 jobs** (+37)
- **32 total companies**
- **46.9% success rate** (+9.4%)

### Impact
- ✅ Added 3 more companies
- ✅ Increased job count by 37
- ✅ Improved success rate to nearly 50%
- ✅ Proved headless browser approach works

---

## 💡 Next Steps (Optional)

### Fix Certara
- Debug the CSS selectors
- Inspect page structure
- May need different approach

### Add More Headless Scrapers
Could add for these companies (from earlier list):
- Shopify (major company)
- Toast (growing company)
- Guidewire (insurance software)
- Others from the 14-company list

### Optimize Performance
- Run headless scrapers in parallel
- Cache ChromeDriver
- Reduce wait times where possible

---

## 🏆 Success Metrics

✅ **Built 4 headless scrapers**
✅ **3 working successfully** (75% success rate)
✅ **Added 37 more jobs**
✅ **Now at 15/32 companies** (46.9%)
✅ **Proven approach for JavaScript-heavy sites**

The headless browser framework is now in place and can be extended to more companies as needed!
