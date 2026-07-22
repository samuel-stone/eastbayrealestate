# Release Notes v4.8.1

## Redfin Scraper Stabilization & Property Data Model Migration

**Release Date:** 2026-07-22

## Overview

v4.8.1 transitions the scraping pipeline from the deprecated `scraped_leads` workflow into the unified `leads → properties → marketplace_signals` architecture.

This release establishes the foundation for a more scalable real estate intelligence platform by separating:

- Canonical property entities
- Lead generation opportunities
- External marketplace observations
- AI enrichment workflows

## Major Changes

### 1. Redfin Scraper Architecture Migration

The Redfin scraping worker was updated to remove dependency on the obsolete `scraped_leads` table.

Previous flow:

```
scraped_leads
      |
      v
Redfin scraper
      |
      v
properties
```

New flow:

```
leads
  |
  v
redfin_scrape_queue
  |
  v
Redfin scraper
  |
  v
properties
  |
  v
marketplace_signals
```

### 2. Database Model Evolution

Added property relationship support:

```sql
leads.property_id
        |
        v
properties.id
```

This creates a normalized relationship between:

- Properties as the canonical asset record
- Leads as outreach opportunities
- Marketplace signals as external observations

### 3. Property Enrichment Foundation

The architecture now supports future Redfin/Zillow enrichment fields:

- Listing URL
- Price history
- Beds
- Baths
- Square footage
- Days on market
- Price reductions
- Fixer/investor indicators
- Last scraped timestamp

## 4. Redfin Queue Development

Added `redfin_scrape_queue` abstraction to generate scraping candidates dynamically.

Current queue logic supports:

- Address-based Redfin search generation
- City filtering
- Property enrichment workflows
- Future prioritization scoring

## 5. Local AI Performance Improvements

Switched local AI architecture from:

```
qwen3-coder:30b
```

to:

```
llama3.2:3b
```

Benefits:

- Faster inference
- Lower memory usage
- Better Mac hardware compatibility
- More reliable automated post-commit workflows

Validated:

- Ollama API response success
- AI proposal generation
- Agent memory persistence
- Automated architecture reporting

## 6. Automation Engine Compatibility

Verified compatibility with:

- Job scheduler
- Worker execution flow
- AI enrichment tasks
- Post-commit reporting pipeline

Redfin jobs continue completing successfully through the automation engine.

## Database Changes

Added:

```sql
ALTER TABLE leads
ADD COLUMN property_id INTEGER REFERENCES properties(id);

ALTER TABLE leads
ADD COLUMN source_type TEXT;
```

## Known Limitations

- Existing assessor parcel imports still dominate `last_source_url`.
- Redfin URL discovery requires dedicated marketplace ingestion logic.
- Scraping queue prioritization will be expanded in future releases.

## Roadmap

### v4.9

Frontend improvements:

- Lead/property visualization
- Scraper health dashboard
- Enrichment monitoring

### v5.0

Platform architecture:

- Full property normalization
- Remote Ollama worker architecture
- Dedicated Mac Mini AI inference worker
- Predictive seller scoring pipeline

## Validation

Completed checks:

✅ Python compilation successful  
✅ Redfin worker executes successfully  
✅ Automation jobs completing  
✅ Database migrations applied  
✅ Ollama AI workflow validated  
✅ Agent memory persistence verified

---

**Summary**

v4.8.1 moves the platform from a scraper prototype into a normalized real estate intelligence system capable of combining public records, marketplace data, and AI-driven seller prediction.
