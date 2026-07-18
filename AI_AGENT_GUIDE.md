# AI Agent Guide: EastBayRealEstate v1.0

This guide defines the operational roles of the AI agents and provides a protocol for debugging.

## 1. Context & Scope
* **Mission**: Automate real estate lead generation in the East Bay through data ingestion, semantic classification, and actionable reporting[cite: 3].
* **Tech Stack**: Python 3, SQLite, Pandas, `smtplib`, and GitHub[cite: 3].
* **Project Structure**:
    * `/prospect_model`: Core logic (Semantic Engine/Batch Loader)[cite: 3].
    * `/scraper`: Data collection (Walnut Creek, Danville)[cite: 3].
    * `/queries`: SQL analytic definitions[cite: 3].
    * `/output`: CSV report exports[cite: 3].

## 2. Agent Operational Roles
* **Data Ingestion Agent (`batch_load_permits.py`)**: Synchronizes raw PDF permit data into `leads.sqlite3`[cite: 3].
* **Semantic Agent (`semantic_engine.py`)**: Classifies projects into "Expansion," "Renovation," or "Systems"[cite: 3].
* **Analytics Agent (`run_reports.py`)**: Generates structured reports via SQL queries in `/queries`[cite: 3].

## 3. Debugging Protocol (Scrapers)
If `scrape_danville.py` or `scrape_walnut_creek.py` fails:
1. **Check Connectivity**: Verify network access and proxy settings[cite: 3].
2. **Inspect Headers**: Run `scraper/debug_headers.py` to ensure request headers (User-Agent) are not being blocked[cite: 3].
3. **Verify DOM**: If the structure changed, use `scraper/debug_wc_html.py` to inspect the current HTML and update parsing logic[cite: 3].
4. **Log Analysis**: Review the output in `scraper/output/` for specific error codes or incomplete data sets[cite: 3].

## 4. Rules & Constraints
* **Security**: Never hardcode API keys[cite: 3].
* **Workflow**: Run `git add -A` and commit descriptive messages before pushing to `main`[cite: 3].
* **Reference**: Always consult `docs/planning/QUARTERLY_ROADMAP_Q3_2026.md` for current project priorities[cite: 3].
