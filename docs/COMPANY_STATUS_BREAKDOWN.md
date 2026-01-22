# Company Scraper Status & Effort Analysis

Complete breakdown of all 32 companies with scraper status and implementation effort.

---

## ✅ Working Companies (11/32) - 34% Success Rate

These companies are **fully operational** and scraping successfully.

| # | Company | Jobs | Platform | Scraper | Effort to Maintain |
|---|---------|------|----------|---------|-------------------|
| 1 | **Veeva** | 945 | Custom | `veeva_scraper.py` | ⚪ Low - Custom, stable |
| 2 | **Workday** | 40 | Workday API | `workday_scraper.py` | ⚪ Low - API stable |
| 3 | **Autodesk** | 40 | Workday API | `workday_scraper.py` | ⚪ Low - API stable |
| 4 | **Q2** | 40 | Workday API | `workday_scraper.py` | ⚪ Low - API stable |
| 5 | **Workiva** | 40 | Workday API | `workday_scraper.py` | ⚪ Low - API stable |
| 6 | **nCino** | 36 | Workday API | `workday_scraper.py` | ⚪ Low - API stable |
| 7 | **SPS Commerce** | 35 | Workday API | `workday_scraper.py` | ⚪ Low - API stable |
| 8 | **Alkami** | 32 | Workday API | `workday_scraper.py` | ⚪ Low - API stable |
| 9 | **Manhattan Associates** | 30 | Workday API | `workday_scraper.py` | ⚪ Low - API stable |
| 10 | **CCC Intelligent Solutions** | 20 | Workday API | `workday_scraper.py` | ⚪ Low - API stable |
| 11 | **Vertex** | 18 | Workday API | `workday_scraper.py` | ⚪ Low - API stable |
| 12 | **Bill.com** | 46 | Greenhouse API | `greenhouse_scraper.py` | ⚪ Low - API stable |

**Total Jobs:** ~1,322 jobs

---

## ❌ Non-Working Companies (21/32) - 66% Failure Rate

### 🟢 LOW EFFORT (2 companies) - Quick Wins

These can be fixed with **configuration changes** or **simple platform scrapers**.

| # | Company | Platform | Issue | Solution | Effort | Estimated Time |
|---|---------|----------|-------|----------|--------|----------------|
| 13 | **Kinaxis** | iCIMS | Need platform scraper | Build `icims_scraper.py` | 🟢 LOW | 30-60 min |
| 14 | **Ensono** | UltiPro/UKG | Need platform scraper | Build `ultipro_scraper.py` | 🟢 LOW | 30-60 min |

**Details:**
- **Kinaxis (iCIMS)**:
  - URL pattern: `careers-kinaxis.icims.com`
  - iCIMS is a common ATS platform
  - Likely has API or parseable HTML
  - Similar approach to Greenhouse/Lever

- **Ensono (UltiPro)**:
  - URL pattern: `recruiting.ultipro.com/ONE1018ONSO/JobBoard/...`
  - UltiPro (now UKG) is HR platform
  - Need to investigate API endpoints
  - May have JSON data embedded

**ROI:** 🟢 **HIGH** - Platform scrapers can be reused for other companies using same ATS

---

### 🟡 MEDIUM EFFORT (14 companies) - Headless Browser Required

These sites use **heavy JavaScript** and require browser automation (Selenium/Playwright).

| # | Company | URL Pattern | Estimated Effort | Time | Worth It? |
|---|---------|-------------|-----------------|------|-----------|
| 15 | **Procore** | careers.procore.com | 🟡 MEDIUM | 2-3 hrs | ⭐⭐⭐ Major company |
| 16 | **Shopify** | shopify.com/careers | 🟡 MEDIUM | 2-3 hrs | ⭐⭐⭐ Major company |
| 17 | **Toast** | careers.toasttab.com | 🟡 MEDIUM | 2-3 hrs | ⭐⭐ Growing company |
| 18 | **Guidewire** | guidewire.com/careers | 🟡 MEDIUM | 2-3 hrs | ⭐⭐ Enterprise software |
| 19 | **BlackLine** | careers.blackline.com | 🟡 MEDIUM | 2-3 hrs | ⭐⭐ FinTech |
| 20 | **AppFolio** | appfolio.com/open-roles | 🟡 MEDIUM | 2-3 hrs | ⭐ Property management |
| 21 | **Certara** | careers.certara.com | 🟡 MEDIUM | 2-3 hrs | ⭐ Life sciences |
| 22 | **Simulations Plus** | simulations-plus.com/career | 🟡 MEDIUM | 2-3 hrs | ⭐ Pharma software |
| 23 | **Altus Group** | careers.altusgroup.com | 🟡 MEDIUM | 2-3 hrs | ⭐ Commercial real estate |
| 24 | **Tyler Technologies** | tylertech.com/careers | 🟡 MEDIUM | 2-3 hrs | ⭐⭐ GovTech |
| 25 | **Bentley** | jobs.bentley.com | 🟡 MEDIUM | 2-3 hrs | ⭐⭐ Infrastructure software |
| 26 | **Nemetschek** | nemetschek.com/career | 🟡 MEDIUM | 2-3 hrs | ⭐ Design/construction |
| 27 | **Dassault Systemes (3DS)** | 3ds.com/careers | 🟡 MEDIUM | 2-3 hrs | ⭐⭐⭐ Major PLM company |
| 28 | **Descartes** | careers.descartes.com | 🟡 MEDIUM | 2-3 hrs | ⭐ Supply chain |

**What's Required:**
1. Install Selenium or Playwright
2. Create `headless_scraper.py` base class
3. For each company:
   - Load page in headless browser
   - Wait for JavaScript to render jobs
   - Parse DOM for job listings
   - Handle pagination

**Pros:**
- Can scrape any JavaScript-heavy site
- More reliable once set up
- Reusable headless base class

**Cons:**
- Requires Chrome/Firefox driver
- Slower execution (browsers are heavy)
- More complex error handling
- Higher resource usage
- Maintenance overhead (sites change frequently)

**ROI:** 🟡 **MEDIUM** - Worth it for major companies (Procore, Shopify, 3DS), less so for smaller ones

---

### 🔴 HIGH EFFORT / NOT RECOMMENDED (5 companies)

These have **significant barriers** and are **not worth pursuing**.

| # | Company | Issue | Why Not Worth It | Recommendation |
|---|---------|-------|------------------|----------------|
| 29 | **HubSpot** | Third-party redirect | Redirects to RippleMatch platform | ⛔ SKIP |
| 30 | **Salesforce** | Bot detection (400 error) | Aggressive anti-scraping measures | ⛔ SKIP |
| 31 | **ServiceNow** | Bot detection (403 Forbidden) | Blocks automated requests | ⛔ SKIP |
| 32 | **Axon** | SSL certificate issues | Technical SSL problems | ⛔ SKIP |

**Details:**

- **HubSpot**:
  - Redirects to `app.ripplematch.com`
  - Would require scraping third-party platform
  - Violates RippleMatch's terms likely
  - Jobs not on HubSpot's own site
  - **Effort:** 🔴 HIGH
  - **Recommendation:** ⛔ **SKIP** - Not worth it

- **Salesforce**:
  - Returns 400 Bad Request
  - Likely has bot detection
  - Would need sophisticated anti-detection
  - Rotating IPs, browser fingerprinting, etc.
  - **Effort:** 🔴 HIGH
  - **Recommendation:** ⛔ **SKIP** - Too much effort

- **ServiceNow**:
  - Returns 403 Forbidden
  - Active bot protection
  - Similar challenges to Salesforce
  - **Effort:** 🔴 HIGH
  - **Recommendation:** ⛔ **SKIP** - Too much effort

- **Axon**:
  - SSL certificate verification fails
  - Could bypass with SSL verification disabled
  - But likely indicates other technical issues
  - **Effort:** 🟡 MEDIUM (technical workaround)
  - **Recommendation:** ⛔ **SKIP** - Low priority

**ROI:** 🔴 **VERY LOW** - Not recommended

---

## 📊 Summary Statistics

### Current Status
- ✅ **Working:** 12 companies (37.5%)
- ❌ **Not Working:** 20 companies (62.5%)
- **Total Jobs Captured:** ~1,322 jobs

### Effort Distribution
- 🟢 **Low Effort:** 2 companies (10% of failed) - 30-60 min each
- 🟡 **Medium Effort:** 14 companies (70% of failed) - 2-3 hrs each
- 🔴 **High Effort:** 4 companies (20% of failed) - Not recommended

### Potential Additional Companies by Effort

| Effort Level | Companies | Time Investment | Additional Jobs (Est.) | ROI |
|--------------|-----------|-----------------|----------------------|-----|
| 🟢 Low | 2 | 1-2 hours | ~50-150 | ⭐⭐⭐⭐⭐ Excellent |
| 🟡 Medium | 14 | 28-42 hours | ~400-800 | ⭐⭐⭐ Good (if prioritized) |
| 🔴 High | 4 | Unknown | ~100-300 | ⭐ Poor |

---

## 🎯 Recommended Action Plan

### Phase 1: Quick Wins (RECOMMENDED) ✅
**Effort:** 1-2 hours
**Gain:** 2 companies, ~50-150 jobs

1. Build `icims_scraper.py` for **Kinaxis**
2. Build `ultipro_scraper.py` for **Ensono**

**Why:** Platform scrapers can be reused for future companies.

---

### Phase 2: High-Value Headless Browsers (OPTIONAL)
**Effort:** 6-9 hours
**Gain:** 3 companies, ~150-300 jobs

Focus on major companies only:
1. **Procore** - Major construction tech company
2. **Shopify** - Major e-commerce platform
3. **Dassault Systemes** - Major PLM/CAD company

**Why:** High brand recognition, likely lots of jobs.

---

### Phase 3: Remaining Medium Effort (IF NEEDED)
**Effort:** 20-30 hours
**Gain:** 11 companies, ~250-500 jobs

Implement headless scraper for:
- Toast, Guidewire, BlackLine, AppFolio, Certara
- Simulations Plus, Altus, Tyler Tech, Bentley
- Nemetschek, Descartes

**Why:** Only if you need comprehensive coverage.

---

### Phase 4: Skip High-Effort Companies ⛔
**Companies to Skip:** HubSpot, Salesforce, ServiceNow, Axon

**Why:** Not worth the effort, technical barriers too high.

---

## 🔧 Implementation Guide by Effort

### 🟢 LOW EFFORT - Platform Scrapers

**Example: iCIMS Scraper**

```python
# scrapers/icims_scraper.py
class ICIMSScraper(BaseScraper):
    def scrape(self):
        # Research iCIMS API
        # Likely pattern: careers-COMPANY.icims.com/jobs/search
        # Look for JSON data or API endpoint
        pass
```

**Steps:**
1. Visit Kinaxis careers page
2. Open DevTools → Network tab
3. Look for API calls with job data
4. Build scraper using discovered endpoint
5. Test and iterate

**Time:** 30-60 minutes per platform

---

### 🟡 MEDIUM EFFORT - Headless Browser

**Example: Headless Scraper Base**

```python
# scrapers/headless_scraper.py
from selenium import webdriver
from scrapers.base_scraper import BaseScraper

class HeadlessScraper(BaseScraper):
    def scrape(self):
        driver = webdriver.Chrome()  # or Firefox
        driver.get(self.url)
        # Wait for jobs to load
        # Parse DOM
        # Extract job data
        driver.quit()
        return jobs
```

**Steps:**
1. Install: `pip install selenium`
2. Download ChromeDriver
3. Create base headless scraper class
4. Implement company-specific scrapers
5. Test each site

**Time:** 2-3 hours per company (after base class built)

---

### 🔴 HIGH EFFORT - Bot Detection Bypass

**NOT RECOMMENDED**

Requires:
- Rotating proxies
- Browser fingerprint randomization
- CAPTCHA solving services
- Extensive testing
- Ongoing maintenance

**Time:** 10+ hours, ongoing maintenance

---

## 💡 My Recommendation

### Best ROI Strategy:

1. ✅ **Use current 12 working companies** (1,322+ jobs)
   - Already done, zero effort
   - Reliable, low maintenance
   - Good coverage

2. 🟢 **Add 2 platform scrapers** (1-2 hours)
   - Kinaxis (iCIMS)
   - Ensono (UltiPro)
   - Gets you to 14 companies
   - Platform scrapers are reusable

3. 🟡 **Optionally add 3 headless scrapers** (6-9 hours)
   - Procore, Shopify, Dassault (high-value companies only)
   - Gets you to 17 companies
   - Stop here unless you need more

4. ⛔ **Skip the rest**
   - Not worth time investment
   - Diminishing returns
   - Focus on companies that matter

### Final Numbers:
- **Current:** 12 companies, 1,322 jobs ✅
- **After Phase 1:** 14 companies, ~1,450 jobs
- **After Phase 2:** 17 companies, ~1,650 jobs
- **Maximum Realistic:** ~20 companies out of 32 (62.5%)

**The remaining 12 companies are not worth pursuing.**

---

## 📋 Quick Reference Table

| Status | Count | Action |
|--------|-------|--------|
| ✅ Working | 12 | Use as-is |
| 🟢 Low effort fix | 2 | Build platform scrapers (recommended) |
| 🟡 Medium effort | 14 | Headless browsers (3-5 high-value companies only) |
| 🔴 Skip | 4 | Don't pursue |

**Current ROI:** Excellent (12 companies working)
**Phase 1 ROI:** Very Good (add 2 more)
**Phase 2 ROI:** Good (add 3 more high-value)
**Phase 3 ROI:** Diminishing returns
