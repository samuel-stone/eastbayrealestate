# AI Agent Guide & Rules: EastBayRealEstate v1.0 (PRO-Level)

This document is the "source of truth" for all AI coding assistants (Claude/Copilot/Cursor). 

---

## 1. Project Philosophy & Context
* **Objective**: Transform raw municipal permit data into high-intent real estate outreach signals[cite: 3, 5].
* **Core Loop**: `Scrape` -> `Ingest` -> `Classify` -> `Report` -> `Outreach`[cite: 5].
* **Technical Constraints**: 
    * Strict adherence to SQLite schema integrity[cite: 5].
    * Use Type Hints for all new functions[cite: 5].
    * Keep logic modular to facilitate unit testing[cite: 5].

---

## 2. Agent Operational Roles
* **Ingestion Agent (`batch_load_permits.py`)**: 
    * *Primary Task*: ETL from raw PDFs to `leads.sqlite3`[cite: 3, 5].
    * *Validation Rule*: Ensure no duplicate records based on `permit_id` before commit[cite: 5].
* **Semantic Agent (`semantic_engine.py`)**: 
    * *Primary Task*: Intent classification[cite: 3, 5].
    * *Logic*: Map permit text to `[Expansion, Renovation, Systems, General]`[cite: 3, 5].
* **Analytics Agent (`run_reports.py`)**: 
    * *Primary Task*: Generate weekly high-priority CSV leads[cite: 5].
    * *Logic*: Execute SQL from `/queries` and generate summary stats[cite: 3, 5].

---

## 3. High-Velocity Debugging Protocol (Triage)
If a scraper fails, follow this triage flow:
1. **Connectivity Check**: `ping` or `curl` the target URL first[cite: 5].
2. **Structural Triage**: Run `scraper/debug_wc_html.py`. If tags have changed, **do not** rewrite the scraper. Instead, update the mapping dictionary in the scraper[cite: 3, 5].
3. **Session Triage**: If 403 errors occur, update `scraper/debug_headers.py` with refreshed `User-Agent` strings from your local browser[cite: 3, 5].
4. **Data Integrity**: If DB errors occur, run `sqlite3 leads.sqlite3 "PRAGMA integrity_check;"` to verify database health[cite: 5].

---

## 4. Coding & Prompting Rules
* **New Feature Rule**: Every feature must include a corresponding entry in `docs/planning/QUARTERLY_ROADMAP_Q3_2026.md`[cite: 5].
* **Prompt Engineering Strategy**: 
    * When prompting this codebase, always use the prefix: `[Context: EastBayRealEstate v1.0]`[cite: 5].
    * Ask for **"Pythonic, modular code"** and **"Defensive programming with error logging."**[cite: 5]
* **Git Workflow**: Before any push, verify with `git status`. Always commit with a `[Component] Description` format (e.g., `[Scraper] Fix WC header rotation`)[cite: 3, 5].

---

## 5. Automated Health Checks
Run this sequence to ensure the system is stable:
1. `python scraper/scrape_walnut_creek.py --test`
2. `python prospect_model/semantic_engine.py --dry-run`
3. `python run_reports.py --validate`