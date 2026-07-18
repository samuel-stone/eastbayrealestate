# EastBayRealEstate: Q3 2026 Quarterly Roadmap

This roadmap scales our current pipeline into a full-scale lead generation engine by adding automated outreach and digital presence.

## August 2026: Foundation & Stability (Current Focus)
*   **Engineering**: Fix scraper stability (Danville/Walnut Creek), audit semantic engine, implement robust error logging.
*   **Output**: Daily CSV reports via `run_reports.py`.
*   **Planning**: Finalize project structure and v1.0 documentation.
*   **Infrastructure -- Phase 1 (this phase)**: Migrate the database from local SQLite to a managed
    Postgres instance on Railway, using Railway's free trial credit. Scripts continue running
    locally (on Sam's machine) against the remote database -- no code is deployed to Railway yet.
    Scope: schema translation, one-time data migration, and updating all `sqlite3`-based database
    code (`base.py`, `score_prospects.py`, `batch_load_permits.py`, `run_reports.py`,
    `export_leads.py`, and others) to use Postgres instead.

## Phase 2 (Deferred -- Future Quarter): Full Railway Deployment
*   **Scope**: Deploy the scrapers and scoring pipeline (`scrape_walnut_creek.py`, `scrape_danville.py`,
    `batch_load_permits.py`, `score_prospects.py`) to Railway itself as Dockerized Cron Job services,
    running on a schedule instead of manually from a local machine.
*   **Why deferred**: Running Playwright-based browser automation on Railway requires paid usage
    beyond the free trial credit (Railway recommends at least 1GB memory per Playwright service).
    Combined with the Postgres database from Phase 1, realistic ongoing cost is estimated at
    roughly $15-30+/month -- worth doing once the pipeline's value justifies that recurring cost,
    not before.
*   **Trigger to revisit**: Once Phase 1 is stable and there's a clear case (e.g., outreach volume
    or lead quality) that justifies moving off manual local runs.

## September 2026: Automated Outreach Engine
*   **Outreach Integration**: 
    *   Connect lead reports to an email automation tool (e.g., Mailgun or Gmail API).
    *   Draft personalized email templates based on `intent_category` (e.g., specific "Expansion" project messaging).
    *   Build a "Lead Outreach Tracker" to log contacted status and follow-ups.
*   **Infrastructure**: 
    *   Set up a database table for outreach status to prevent duplicate contact.

## October 2026: SEO & Digital Presence
*   **Content Generation**: 
    *   Use AI to generate neighborhood-specific real estate insights based on collected permit data.
    *   Create static landing pages for high-demand areas (e.g., "ADU Trends in Walnut Creek").
*   **SEO Strategy**:
    *   Structure the site to target local real estate investment keywords.
    *   Automate blog post publishing for your Substack or professional site using the data insights gathered from the weekly pipeline.

## Success Metrics
*   **Weekly**: 100% successful permit data ingestion.
*   **Monthly**: Outreach to 50+ high-intent "Expansion/Renovation" leads.
*   **Quarterly**: Launch of 3+ data-driven landing pages and automated newsletter.