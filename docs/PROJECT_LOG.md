# East Bay Real Estate Monitoring Project

## Overview
Automated scraping and analysis of municipal building permit data in the East Bay, starting with Walnut Creek.

## Version History
### v1.1 - The "Stable Scraper" Release
*   **Status**: Stable, functional extraction.
*   **Key Fixes**:
    *   Replaced raw JS injection with Playwright `locator` API.
    *   Fixed `DateTime` validation error by clearing input fields via DOM injection before setting dates.
    *   Implemented full-history scraping via pagination loop ("Next >" detection).
    *   Structured raw table output into Python dictionaries.

---

## Technical Roadmap (In-Progress)
### v1.2 - Database Migration (Current Sprint)
*   **Objective**: Migrate from local SQLite to hosted PostgreSQL.
*   **Action Items**:
    *   [ ] Configure `SQLAlchemy` for database-agnostic connection.
    *   [ ] Define schema for `permits` table.
    *   [ ] Move credentials to environment variables.

### v1.3 - Automation & Deployment
*   **Objective**: Cloud-based automated execution.
*   **Action Items**:
    *   [ ] Deploy to Railway/Supabase.
    *   [ ] Schedule daily execution (Cron/GitHub Actions).

---

## Known Issues
*   **UI Sensitivity**: Current scraper assumes Walnut Creek portal UI remains static.
*   **Dependency Management**: Moving towards containerization for cloud readiness.