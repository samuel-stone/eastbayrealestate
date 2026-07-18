This is the handoff guide for the eastbayrealestate project. The goal is to help Deborah Stone generate real-estate leads with a practical, public-data workflow that stays compliant and useful.

## Current project goal
Create a simple lead-generation system that helps Deborah attract buyers, sellers, and relocation-minded prospects in Walnut Creek and nearby East Bay neighborhoods.

## Current implementation state
The scraper has moved beyond generic page metadata. It now supports a property-search-first workflow that:
- reads a plain-text list of addresses or queries,
- calls the public PublicRecordsData address-search endpoint,
- returns structured property rows with address, city, parcel information, and a lead score,
- exports the results as CSV or JSON.

## Recommended workflow for the next agent
1. Review the project document and the scraper before editing anything.
2. Use the scraper to build a prospect queue from a list of addresses.
3. Review the ranked CSV and select the strongest addresses for a full property-report request.
4. Keep the project modular and document every workflow change.

## Scraper guidance
The main implementation lives in scraper/scrape_public_data.py.

### Current files
- scraper/scrape_public_data.py: main scraper logic
- scraper/tests/test_scrape_public_data.py: regression tests
- scraper/contra_costa_targets.json: sample targets for county and city-related sources
- scraper/output/: export directory for generated CSV and JSON files

### Commands to use
Run the tests:
```bash
pytest -q scraper/tests/test_scrape_public_data.py
```

Run the scraper with a text file of addresses or queries:
```bash
python3 scraper/scrape_public_data.py --queries-file scraper/addresses.txt --output scraper/output/contra_costa_prospects.csv
```

## Important notes
- Keep the workflow conservative and public-only.
- Preserve source URLs, timestamps, and a clear audit trail.
- Use the project document as the primary scope document.
- The next phase is the asynchronous property-report request stage for the highest-value addresses.
