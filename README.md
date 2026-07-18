# EastBayRealEstate: Property Prospecting & Analytics

## 1. Project Philosophy & Context
* **Objective**: Transform raw municipal permit data into high-intent real estate outreach signals.
* **Scale**: Pulls from public data (tax assessor and property permit records) to create and enhance a **350,000+ address record database**. 
* **Coverage**: Actively tracking Contra Costa County cities including Walnut Creek, Concord, Orinda, and Lafayette to identify renovations, house flips, and new construction over the last two decades.
* **Core Loop**: `Scrape` -> `Ingest` -> `Classify` -> `Report` -> `Outreach`.
* **Technical Constraints**: Strict adherence to SQLite schema integrity and modular, type-hinted Python code.

## 2. Technology Stack & Architecture
* **Web Automation**: Playwright (Python Sync API) via Headless Chromium for robust ASP.NET scraping and JavaScript-heavy DOM extraction.
* **Data Processing**: Python 3 orchestrates the ETL pipeline, using injected ES6 JavaScript to bypass Playwright memory leaks during massive archival runs.
* **Storage**: Local SQLite leveraging `INSERT OR IGNORE` for idempotent, crash-proof data staging. Planned migration to cloud-hosted PostgreSQL (Railway).

## 3. Operational Guide

### Agent Roles
* **Ingestion Agent (`batch_load_permits.py`)**: ETL from PDFs to `leads.sqlite3`.
* **Semantic Agent (`semantic_engine.py`)**: Classifies projects into `[Expansion, Renovation, Systems, General]`.
* **Analytics Agent (`run_reports.py`)**: Generates structured reports via SQL queries in `/queries`.

### Scraper Workflows & CLI Commands
**GIS Parcel Integration**
Processes monthly Contra Costa County parcel GIS downloads:
```bash
python3 scraper/scrape_public_data.py --parcels-url "<zip_url>" --database scraper/output/leads.sqlite3