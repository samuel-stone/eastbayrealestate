# EastBayRealEstate: Property Prospecting & Analytics

## 1. Project Philosophy & Context
* **Objective**: Transform raw municipal permit data into high-intent real estate outreach signals.
* **Core Loop**: `Scrape` -> `Ingest` -> `Classify` -> `Report` -> `Outreach`.
* **Technical Constraints**: Strict adherence to SQLite schema integrity and modular, type-hinted Python code.

## 2. Operational Guide
### Scraper Workflows
* **Property-Search**: Turns lists of addresses/queries into search requests.
* **GIS Integration**: Processes monthly Contra Costa County parcel GIS downloads.
* **Run Command**: `python3 scraper/scrape_public_data.py --parcels-url "<zip_url>" --database scraper/output/leads.sqlite3`

### Agent Roles
* **Ingestion Agent (`batch_load_permits.py`)**: ETL from PDFs to `leads.sqlite3`.
* **Semantic Agent (`semantic_engine.py`)**: Classifies projects into `[Expansion, Renovation, Systems, General]`.
* **Analytics Agent (`run_reports.py`)**: Generates structured reports via SQL queries in `/queries`.

## 3. High-Velocity Debugging Protocol
If a scraper fails, follow this triage flow:
1. **Connectivity**: `ping` or `curl` the target URL first.
2. **Structural Triage**: Run `scraper/debug_wc_html.py`. Update mapping dictionaries, do not rewrite logic.
3. **Session Triage**: Refresh `User-Agent` strings in `scraper/debug_headers.py`.
4. **Data Integrity**: Verify health via `sqlite3 leads.sqlite3 "PRAGMA integrity_check;"`.

## 4. Coding & Prompting Rules
* **New Feature Rule**: Must include a corresponding entry in `docs/planning/QUARTERLY_ROADMAP_Q3_2026.md`.
* **Prompt Engineering**: Always use the prefix: `[Context: EastBayRealEstate v1.0]`.
* **Git Workflow**: Always commit with a `[Component] Description` format.
