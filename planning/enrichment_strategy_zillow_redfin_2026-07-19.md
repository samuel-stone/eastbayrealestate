# Data Enrichment Strategy: Zillow_Redfin
**Date Generated:** 2026-07-19

## Objective
Need to bypass Cloudflare/DataDome gates to acquire deeper property history and valuation estimates.

## Proposed Bypass & Integration Architecture
### 1. Identity Masking
- Implement residential proxy rotation (e.g., BrightData, Smartproxy) to distribute requests and avoid IP bans.
- Use `undetected-chromedriver` or `Playwright` to simulate human interaction, ensuring proper TLS fingerprinting.

### 2. Data Extraction
- Avoid parsing DOM HTML where possible. Instead, intercept the internal XHR/Fetch API JSON payloads using browser network tools.
- Introduce randomized delays (`time.sleep` between 3-9 seconds) and non-linear mouse movements.

### 3. Alternative Fallbacks
- If frontend scraping fails, evaluate secondary APIs like ATTOM Data or RentCast for backend data enrichment.
