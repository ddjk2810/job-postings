# Failed Companies Analysis & Solutions

This document analyzes the 21 companies that failed in the initial scraping run and provides solutions for each.

## Summary of Results

- **Total Companies**: 32
- **Successful**: 11 (1,276 jobs)
- **Failed**: 21 (need custom scrapers or headless browsers)

---

## Platform Categories

### ✅ Can Be Fixed with Platform Scrapers

#### 1. **Greenhouse Platform** (API Available)

**Companies Using Greenhouse:**
- Bill.com

**Solution:** Use `greenhouse_scraper.py` (already built)

**Configuration Needed:**
```json
{
  "scraper": "greenhouse_scraper",
  "greenhouse_id": "billcom"
}
```

**How to Find greenhouse_id:**
- Visit the careers page
- Look for URLs like `boards.greenhouse.io/COMPANY_ID`
- Or check the embedded iframe src

---

#### 2. **Lever Platform** (API Available)

**Companies Using Lever:**
- (None identified yet in failed list, but scraper ready)

**Solution:** Use `lever_scraper.py` (already built)

**Configuration:**
```json
{
  "scraper": "lever_scraper",
  "lever_id": "companyname"
}
```

---

### ⚠️ Require Headless Browser (JavaScript-Heavy)

These sites load jobs dynamically via JavaScript and need Selenium/Playwright:

1. **Procore** - Custom Rails/Turbo app
   - URL: careers.procore.com/jobs/search
   - Platform: Custom Rails with Hotwired Turbo
   - Needs: Headless browser to render JS

2. **Shopify** - JavaScript loaded
   - URL: www.shopify.com/careers
   - Platform: Custom React/Vue app
   - Needs: Headless browser

3. **Toast** - JavaScript loaded
   - URL: careers.toasttab.com/jobs/search
   - Platform: Likely Greenhouse or custom
   - Needs: Investigation or headless browser

4. **Guidewire** - JavaScript loaded
   - URL: www.guidewire.com/about/careers/jobs
   - Platform: Unknown
   - Needs: Headless browser

5. **BlackLine** - JavaScript loaded
   - URL: careers.blackline.com/careers-home/jobs
   - Platform: Unknown
   - Needs: Headless browser

6. **AppFolio** - JavaScript loaded
   - URL: www.appfolio.com/open-roles
   - Platform: Unknown
   - Needs: Headless browser

7. **Certara** - JavaScript loaded
   - URL: careers.certara.com/jobs
   - Platform: Unknown
   - Needs: Headless browser

8. **Simulations Plus** - JavaScript loaded
   - URL: www.simulations-plus.com/career-center
   - Platform: Unknown
   - Needs: Headless browser

9. **Altus Group** - JavaScript loaded
   - URL: careers.altusgroup.com/global/en
   - Platform: Unknown
   - Needs: Headless browser

10. **Tyler Technologies** - JavaScript loaded
    - URL: www.tylertech.com/careers/job-openings
    - Platform: Unknown
    - Needs: Headless browser

11. **Bentley** - JavaScript loaded
    - URL: jobs.bentley.com/search
    - Platform: Unknown
    - Needs: Headless browser

12. **Nemetschek** - JavaScript loaded
    - URL: www.nemetschek.com/en/company/career
    - Platform: Unknown
    - Needs: Headless browser

13. **Dassault Systemes (3DS)** - JavaScript loaded
    - URL: www.3ds.com/careers/jobs
    - Platform: Unknown
    - Needs: Headless browser

14. **Descartes** - JavaScript loaded
    - URL: careers.descartes.com/join-our-team
    - Platform: Unknown
    - Needs: Headless browser

---

### 🚫 Third-Party Platforms / External Sites

These redirect to external job boards not owned by the company:

1. **HubSpot** - Uses RippleMatch
   - URL: www.hubspot.com/careers/jobs
   - Redirects to: app.ripplematch.com
   - Platform: RippleMatch (third-party)
   - Solution: Would need to scrape RippleMatch (not recommended)

---

### 🔒 Bot Protection / Access Denied

These sites actively block automated requests:

1. **ServiceNow** - 403 Forbidden
   - URL: careers.servicenow.com/jobs
   - Error: 403 Client Error
   - Needs: More sophisticated headers/proxy/headless browser

2. **Salesforce** - 400 Bad Request
   - URL: careers.salesforce.com/en/jobs
   - Error: 400 error (possible bot detection)
   - Needs: Headless browser or proper headers

3. **Axon** - SSL Certificate Error
   - URL: www.axon.com/careers/all
   - Error: SSL certificate verification failed
   - Needs: SSL cert handling or different approach

---

### ❓ Unknown Platform (Need Investigation)

These need further investigation to determine the best approach:

1. **Kinaxis** - iCIMS platform
   - URL: careers-kinaxis.icims.com
   - Platform: iCIMS ATS
   - Needs: iCIMS API research

2. **Ensono** - UltiPro platform
   - URL: recruiting.ultipro.com/ONE1018ONSO/JobBoard/...
   - Platform: UltiPro/UKG
   - Needs: UltiPro API research

---

## Recommended Action Plan

### Phase 1: Quick Wins (Platform Scrapers) ✅

**Already Built:**
- Greenhouse scraper
- Lever scraper

**Action:**
Update company configs with platform IDs where known.

### Phase 2: Research Additional Platforms

Build scrapers for:
1. **iCIMS** (for Kinaxis)
2. **UltiPro/UKG** (for Ensono)

### Phase 3: Headless Browser Implementation (Optional)

For the 14+ companies requiring JavaScript rendering:
- Use Selenium or Playwright
- Create a headless browser base class
- Implement company-specific scrapers

**Pros:**
- Can scrape any site
- More reliable for JS-heavy sites

**Cons:**
- Slower (browsers are heavy)
- More complex setup
- Requires Chrome/Firefox installed
- Higher resource usage

### Phase 4: Skip Unrealistic Targets

**Do NOT pursue:**
- HubSpot (RippleMatch redirect)
- Sites with aggressive bot protection (unless critical)

---

## Implementation Status

### ✅ Working (11 companies)
- Veeva (custom scraper)
- 10 Workday companies (workday_scraper)

### 🟡 Fixable with Config Updates (1 company)
- Bill.com (need to add greenhouse_id)

### 🔴 Need Headless Browser (14+ companies)
- Most JavaScript-heavy sites

### ⛔ Skip / Not Recommended (3 companies)
- HubSpot (third-party redirect)
- ServiceNow (bot protection)
- Axon (SSL issues)

---

## How to Add Platform IDs

### Finding Greenhouse ID:
1. Visit careers page
2. Open browser DevTools (F12)
3. Look in Network tab for requests to `boards-api.greenhouse.io`
4. Or check iframe src for pattern: `for=COMPANY_ID`

### Finding Lever ID:
1. Visit careers page
2. Look for URLs like `jobs.lever.co/COMPANY_NAME`
3. The company name in the URL is the lever_id

### Finding iCIMS ID:
1. Visit careers page
2. Look for URLs like `careers-COMPANY.icims.com`
3. May require additional API endpoint research

---

## Next Steps

1. ✅ Built Greenhouse & Lever scrapers
2. Update Bill.com config with greenhouse_id
3. Test updated configurations
4. Document headless browser approach for remaining companies
5. Decide which companies are worth the headless browser effort

---

## Effort vs. Value Assessment

**High Value, Low Effort:**
- Bill.com (just needs config update)

**High Value, Medium Effort:**
- Companies using iCIMS or UltiPro (need platform scrapers)

**Medium Value, High Effort:**
- JavaScript-heavy sites (need headless browser)

**Low Value:**
- Third-party redirects
- Sites with aggressive bot protection
