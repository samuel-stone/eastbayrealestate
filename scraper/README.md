# Property-First Public Scraper

This folder contains a local-first scraper for public property prospecting in Contra Costa County and nearby East Bay jurisdictions.

## What it does
- turns a plain-text list of addresses or queries into property-search requests,
- extracts address and parcel-style fields when present,
- scores records by their usefulness for outreach,
- writes a CSV that can act as a prospective-address list.

## Current workflow
The current source is a public property-search endpoint that returns address and parcel hits. That makes it a good fit for building a prospective-address CSV without buying a paid report.

### Step 1: create a list of addresses
Put one address or query per line in a text file such as:

```text
1116 Fairlawn Ct Walnut Creek CA 94595
123 Main St Concord CA 94520
```

### Step 2: run the scraper
```bash
python3 scraper/scrape_public_data.py --queries-file scraper/addresses.txt --output scraper/output/contra_costa_prospects.csv
```

### Step 3: review the CSV
The generated CSV contains address-based prospect rows with fields such as:
- address
- city
- parcel_number
- lead_rating
- lead_reason
- prospect_type
- data_strength

## Generate address leads from the official parcel download

Contra Costa County publishes a monthly public parcel GIS download. Download the current parcel ZIP from the County GIS download directory, then run:

```bash
python3 scraper/scrape_public_data.py \
  --parcels-file /path/to/Parcels_Public_<month><year>.zip \
  --parcel-cities "Walnut Creek,Lafayette,Orinda" \
  --limit 250 \
  --output scraper/output/parcel_leads.csv
```

This creates property-address candidates without needing an input address list. The public parcel data does not include owner names; any resulting row should remain `needs_review` until a human verifies the signal and any permitted public record.

The importer recognizes the County ZIP's city codes (for example, `WALCR` for Walnut Creek) and writes the full city name to the export.

To download one current public ZIP directly, replace `<current-parcel-zip-url>` with the ZIP link from that directory:

```bash
python3 scraper/scrape_public_data.py \
  --parcels-url "<current-parcel-zip-url>" \
  --parcel-cities "Walnut Creek,Lafayette,Orinda" \
  --limit 250 \
  --output scraper/output/parcel_leads.csv
```

## Keep a lead database and CSV export

Add `--database` to persist leads between runs while keeping the CSV easy to review:

```bash
python3 scraper/scrape_public_data.py \
  --parcels-url "<current-parcel-zip-url>" \
  --parcel-cities "Walnut Creek,Lafayette,Orinda" \
  --limit 250 \
  --output scraper/output/parcel_leads.csv \
  --database scraper/output/leads.sqlite3
```

The database identifies a lead by normalized address and city, preserves a reviewer-set status such as `approved` or `do_not_contact`, and appends a source observation on every run.

## Notes
- Only use public data sources that are openly available.
- Avoid collecting private or sensitive information.
- Respect the website terms of service and robots.txt where applicable.

## Quick start

Install dependencies:

```bash
pip3 install -r scraper/requirements.txt
```

Run the regression tests:

```bash
pytest -q scraper/tests/test_scrape_public_data.py
```

## Next steps
- add more address lists for target neighborhoods,
- enrich the output with permit or planning signals from other public sources,
- turn the CSV into a review-ready prospecting sheet.
