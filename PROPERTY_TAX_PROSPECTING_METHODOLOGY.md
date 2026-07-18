# Property Tax Prospecting Methodology for Contra Costa County

## Purpose

This document defines a practical, compliant approach for building a lead-generation workflow around public property records, tax-related data, and municipal permit activity in Contra Costa County and nearby East Bay jurisdictions.

The goal is to move beyond generic website metadata and toward a scraper and export pipeline that surfaces useful property-level signals such as:

- parcel address
- parcel number
- assessed value
- tax-related activity
- permit or planning activity
- development or business-license signals
- public property or ownership signals where legally and ethically available

This is intended as a prospect-research foundation for real-estate outreach, not as a substitute for licensed data services or a private-contact database.

---

## Current implementation direction
The current workflow is now centered on a two-stage process:

1. Prospecting stage
   - Start with a plain-text list of addresses or queries.
   - Query the public property-search endpoint and build a scored list of property hits.
   - Export those results to CSV or JSON for review.

2. Property-report stage
   - For the highest-value addresses, submit a full property report request via the public property-report workflow.
   - Let the site process the request asynchronously.
   - Save the completed report for outreach and follow-up.

This is more useful than a generic service-page scrape because it generates property-level rows with parcel evidence and a lead score from the start.

---

## Scope of the approach

### In scope

- Publicly accessible county and municipal web pages
- Parcel and property-assessment information that is published for public review
- Building permit, planning, business-license, and related public activity pages
- Publicly posted property or project details that are already intended for public consumption
- Structured CSV/JSON export for review and outreach planning

### Out of scope

- Private records
- Non-public tax documents
- Sensitive personal data beyond what is explicitly public and appropriate to collect
- Scraping behind login walls, gated portals, or any system that requires authentication
- Contact information not clearly intended for public use

---

## Governing principles

1. Public-only, consent-safe workflow
   - Only target pages that are openly accessible and intended for public review.
   - Avoid collecting personal data unless it is clearly part of a public-facing property record and aligns with the project’s limited-use purpose.

2. Minimal and relevant data
   - Prefer parcel-level fields that support outreach: address, parcel, assessed value, property type, tax status, permit activity, and public project signals.
   - Do not collect more than is required for prospecting and review.

3. Respect site rules
   - Honor robots.txt when practical.
   - Use polite request timing and avoid hammering sites.
   - Respect rate limits and temporary blocks.

4. Transparency and auditability
   - Save source URLs and scrape timestamps for every row.
   - Keep a clear record of which source produced each record.

5. Conservative scoring
   - Rank records by the strength of public evidence, not by assumptions.
   - A property record with parcel and assessed value should rank higher than a generic city page.

---

## Practical next steps

1. Keep using the property-search workflow as the first step.
2. Review the highest-scoring rows and submit full property-report requests for the best targets.
3. Preserve the CSV/JSON output as the working lead list.
4. Add more location-specific targets later if the workflow proves useful.

---

## Expected outcome

The intended result is a lead list that is genuinely useful for outreach:

- property address
- parcel and assessed-value information where available
- public permit or planning activity signals
- a clear ranking of which records are strong enough to pursue

That is materially more valuable than a list of website pages or metadata placeholders.
