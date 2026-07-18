# eastbayrealestate — Relocation Signal Improvements

## Background

The current `relocation_signal` field in `scraper/scrape_public_data.py`
(inside `score_prospect()`) is keyword-matching against scraped page text
(looking for words like "relocation," "moving," "new resident," "welcome").
Testing it against real examples shows it almost never fires usefully — it
only labels a lead `relocation_interest` if the scraped page itself happens
to talk about welcoming new residents (e.g. a city's generic welcome page),
which essentially never co-occurs with an actual property lead. In practice
nearly everything falls back to `property_interest` or `none`. It is not
tied to any real fact about a specific property or its owner.

This replaces that keyword-guessing with real, compliant, property-level
public-record signals that actually correlate with an owner having
relocated or being likely to move soon — in the same spirit as the
existing `building_permit_count_24m` / `planning_application_count_24m`
features in `prospect_model/feature_registry.json`.

## New signals to add

1. **Absentee owner flag** — the assessor's mailing address on file differs
   from the property's own (situs) address. Standard public assessor
   field; strongly correlates with an owner who has already relocated.
2. **Homeowner's exemption status** — California assessor rolls indicate
   whether a property currently claims an owner-occupied exemption. Losing
   that exemption often means the owner moved out.
3. **Recent ownership transfer / years since last deed transfer** — county
   recorder deed records are public. A recent transfer, or a very long
   holding period by the same owner, are both established prospecting
   signals.

All three are property-level facts from official records — not personal
or family circumstances — so they stay within the project's existing
compliance boundaries (see `SOURCE_POLICY.md` and the `prohibited_features`
list in `feature_registry.json`).

## Prompt for Claude Code

```
I want to replace the weak keyword-based relocation_signal logic with real 
public-record relocation signals. Please work through this step by step, 
testing as you go:

1. Before writing any scoring logic, investigate what fields are actually 
   available in the Contra Costa Assessor's public parcel download that's 
   already being used (via --inspect-parcels / inspect_parcel_shapefile in 
   scraper/scrape_public_data.py). Specifically check for:
   - A mailing address field separate from the situs/property address
     (commonly named something like MAIL_ADDR, OWNER_ADDR, or similar)
   - A homeowner's exemption indicator field (e.g. HO_EXEMPT, EXEMPTION)
   - A last-transfer or sale-date field (e.g. SALE_DATE, TRANSFER_DATE, 
     DEED_DATE)
   Report back exactly what field names exist and what values they contain 
   (sample a few real records). Do NOT assume these fields exist or guess 
   at their names -- confirm from the actual schema first. If any of the 
   three fields is not present in this data source, say so clearly rather 
   than fabricating a feature from data that isn't there; we may need a 
   different official data source (e.g. the County Recorder's public deed 
   index) for that particular signal.

2. For each field that IS available, add extraction logic to the parcel 
   ingestion path (build_records_from_parcel_shapefile / compose_address 
   area of scraper/scrape_public_data.py) so these values get captured 
   into the record alongside address, city, parcel_number, and 
   assessed_value.

3. Add three new entries to the "allowed_features" list in 
   prospect_model/feature_registry.json, matching the existing style 
   (name, source, level, description):
   - absentee_owner (property level, source: assessor mailing-address field)
   - homeowner_exemption_status (property level, source: assessor exemption field)
   - years_since_last_transfer (property level, source: assessor or recorder 
     transfer-date field)
   Only add the ones for which real data was confirmed available in step 1.

4. Extend prospect_model/score_prospects.py's score_feature_row() to weight 
   these new features into the score, using similar reasoning to how 
   building_permit_count_24m and planning_application_count_24m are 
   weighted today (an absentee owner or a lost homeowner's exemption should 
   meaningfully raise the score; add a short comment explaining the 
   reasoning for each weight so it's easy to review, similar to how the 
   surrounding code already documents itself).

5. Once the new features are wired in, retire the keyword-based 
   relocation_signal logic in scraper/scrape_public_data.py's 
   score_prospect() (the contains_any() checks for "relocation", "moving", 
   "new resident", "new to", "welcome"). Keep score_prospect() focused on 
   what it can honestly determine from a scraped page (property fields, 
   permit/planning keywords), and let the new property-level features in 
   prospect_model handle relocation likelihood instead, since that's a 
   more defensible source of truth.

6. Update prospect_model/README.md and scraper/README.md to document the 
   new features and explain (briefly) why they replaced the old keyword 
   matching.

7. Add test coverage in prospect_model/tests/test_score_prospects.py for 
   the new features: a record with an absentee-owner flag scores higher 
   than one without, a record with a recent transfer scores appropriately, 
   and the tier_for_score() thresholds still make sense with the new 
   scoring range.

After each step, run the existing test suite (pytest scraper/tests 
prospect_model/tests) and fix any breakage before moving to the next item.
```

## Notes on using this

- **Step 1 matters most.** If the Contra Costa parcel download doesn't
  actually expose mailing address, exemption status, or transfer date,
  don't let the coding assistant guess or fabricate placeholder data —
  come back and we can figure out whether the County Recorder's public
  deed index or a different official source covers what's missing.
- This keeps the "relocation" idea, but grounds it in actual public
  property-ownership facts instead of scraped page wording — which also
  means it will work on every property in the parcel dataset, not just the
  rare page that happens to mention "new residents."
