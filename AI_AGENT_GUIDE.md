# AI Agent Guide: EastBayRealEstate v1.0

This guide defines the operational roles of the AI agents and provides a protocol for debugging.

## 1. Context & Scope
* **Mission**: Automate real estate lead generation in the East Bay through data ingestion, semantic classification, and actionable reporting.
* **Tech Stack**: Python 3, SQLite, Pandas, `smtplib`, and GitHub.
* **Project Structure**:
    * `/prospect_model`: Core logic (Semantic Engine/Batch Loader).
    * `/scraper`: Data collection (Walnut Creek, Danville).
    * `/queries`: SQL analytic definitions.
    * `/output`: CSV report exports.

## 2. Agent Operational Roles
* **Data Ingestion Agent (`batch_load_permits.py`)**: Synchronizes raw PDF permit data into `leads.sqlite3`.
* **Semantic Agent (`semantic_engine.py`)**: Classifies projects into "Expansion," "Renovation," or "Systems".
* **Analytics Agent (`run_reports.py`)**: Generates structured reports via SQL queries in `/queries`.

## 3. Debugging Protocol (Scrapers)
If `scrape_danville.py` or `scrape_walnut_creek.py` fails:
1. **Check Connectivity**: Verify network access and proxy settings.
2. **Inspect Headers**: Run `scraper/debug_headers.py` to ensure request headers (User-Agent) are not being blocked.
3. **Verify DOM**: If the structure changed, use `scraper/debug_wc_html.py` to inspect the current HTML and update parsing logic in the main scraper.
4. **Log Analysis**: Review the output in `scraper/output/` for specific error codes or incomplete data sets.

## 4. Rules & Constraints
* **Security**: Never hardcode API keys.
* **Workflow**: Run `git add -A` and commit descriptive messages before pushing to `main`.
* **Reference**: Always consult `docs/planning/QUARTERLY_ROADMAP_Q3_2026.md` for current project priorities.
