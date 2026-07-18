# eastbayrealestate
Lead-generation project for Deborah Stone, Realtor at Compass in Walnut Creek, California.

## Current status
The scraper is an address-first research tool. It produces reviewable property and public-activity leads, retaining the source URL and timestamp for every row. It can retain a name only when an explicitly approved public-record target visibly publishes one; it does not infer owner names or collect contact details.

## What works now
- Reads a plain-text list of addresses or queries from a file via --queries-file
- Queries the public property-search endpoint and returns structured property hits
- Exports results as CSV or JSON for review and outreach planning
- Scores prospects based on address, city, parcel, and property-style signals
- Keeps source type, evidence, and a `needs_review` status for each exported lead

## How to run it
1. Create a text file with one address or query per line, for example: scraper/addresses.txt
2. Run the scraper:
   python3 scraper/scrape_public_data.py --queries-file scraper/addresses.txt --output scraper/output/contra_costa_prospects.csv
3. Review the CSV and select the strongest addresses for the next stage.

## Two-stage workflow
1. Prospecting stage
   - Build a list of target addresses from neighborhoods, relocation patterns, recent transfers, or permit activity.
   - Run the scraper and export the ranked CSV.
2. Review stage
   - Verify each high-ranked row in its official source before outreach.
   - Record a name only where the public record itself displays it and the source is approved in `scraper/contra_costa_targets.json`.
   - Do not collect phone numbers, email addresses, or names from profiles/directories.

## Notes
- Keep the workflow public, compliant, and audit-friendly.
- Preserve source URLs and timestamps in exported rows.
- Treat this as a prospect-research tool, not a private-contact database. The Contra Costa Assessor's online tools do not publish owner names.
