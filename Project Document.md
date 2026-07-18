# eastbayrealestate Project Document

## Project overview
This project is a lead-generation system for Deborah Stone, Realtor at Compass in Walnut Creek, California. The goal is to help her attract local buyers, sellers, and relocation-minded prospects through a practical funnel that combines a landing page, email nurture, and a public-data prospecting workflow.

## Primary objective
Create a launch-ready workflow that:
- introduces Deborah Stone and her value proposition,
- collects leads through an opt-in form,
- nurtures those leads with targeted email content,
- helps identify property-level prospects through public, compliant data collection.

## Current implementation state
The prospecting portion is now working in a more practical form than the original generic page-scraper idea. The project has moved to a two-stage workflow:

1. Prospecting stage
   - Build a queue of addresses or queries from neighborhoods, relocation patterns, or public activity signals.
   - Run the scraper to generate property-search rows with address, city, parcel information, and a lead score.

2. Property-report stage
   - Select the strongest rows.
   - Submit a full property report request through the public property-report workflow.
   - Allow the report to process asynchronously and export the completed report for outreach follow-up.

## Target audience
Primary audiences:
- homeowners considering selling in Walnut Creek, Lafayette, Orinda, Pleasant Hill, Concord, and nearby East Bay neighborhoods,
- buyers searching in the East Bay,
- relocation clients moving into the Bay Area.

## Core deliverables
### 1. Landing page
A simple, polished page that explains Deborah's expertise and includes a strong lead-capture call to action.

### 2. Email series
A short nurture sequence that stays warm, local, and helpful.

### 3. Prospecting workflow
A public-data workflow that:
- stays compliant and conservative,
- uses address-based property-search queries,
- creates a review-ready CSV or JSON export,
- supports manual follow-up and future CRM integration.

## Current scraper workflow
The scraper now accepts a plain-text file of addresses or queries and turns each line into a property-search request.

### Required input
- One address or query per line in a text file.

### Example command
```bash
python3 scraper/scrape_public_data.py --queries-file scraper/addresses.txt --output scraper/output/contra_costa_prospects.csv
```

### Output schema
Each exported row contains:
- source_name
- source_url
- address
- city
- parcel_number
- assessed_value
- activity_date
- notes
- lead_rating
- lead_reason
- relocation_signal
- prospect_type
- data_strength
- scraped_at

## Recommended next steps
1. Build or refine the landing page and opt-in form.
2. Draft the initial email sequence.
3. Continue the property-report stage for the strongest prospects.
4. Keep all workflow notes and commands in this repository so the handoff stays clear.

## Constraints and guidance
- Keep the project focused and simple.
- Prioritize privacy, compliance, and public-only data.
- Avoid private or sensitive data.
- Preserve the audit trail for every lead row.
