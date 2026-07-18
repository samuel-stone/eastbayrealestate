# eastbayrealestate — Codebase Improvement Instructions

Use this as a prompt for Claude Code (or any coding assistant with access to
the repo) to work through these fixes in order. Run the test suite after
each numbered item and fix any breakage before moving to the next one.

```
I want to improve the eastbayrealestate codebase. Please make the following 
changes, testing as you go:

1. POLICY ISSUE (highest priority): In scraper/scrape_public_data.py, the 
   build_records_from_target() function calls an external API at 
   publicrecordsdata.us/api/addresscomplete for "property_search" type 
   targets. This appears to be a commercial people-search/data-broker API, 
   which directly contradicts our own SOURCE_POLICY.md and 
   feature_registry.json, both of which explicitly prohibit 
   "unlicensed listing-site or people-search data." Remove this API 
   integration entirely (the property_search target type and its 
   supporting code), and rely on the official Contra Costa GIS parcel 
   data and permit/planning pages instead. Update contra_costa_targets.json 
   to remove the "publicrecordsdata_sample_address" entry. Remove or update 
   any tests tied to this API.

2. Split scraper/scrape_public_data.py into focused modules:
   - fetch.py: HTML fetching and page-data extraction
   - parcels.py: shapefile/parcel download and parsing
   - scoring.py: score_prospect, build_prospect_row, deduplicate_and_rank_records
   - storage.py: save_results, save_to_database
   - cli.py or keep in scrape_public_data.py: argparse and main()
   Keep the public function names the same so existing tests still pass 
   with updated imports.

3. Remove duplicated "empty error record" dicts (in build_record_from_url 
   and build_records_from_target) by extracting a shared 
   empty_record(source_name, source_type, url, error) helper.

4. Add a short delay (e.g., time.sleep(1)) between sequential HTTP requests 
   when looping over addresses/targets/URLs, so we're not hammering small 
   municipal servers. Make the delay configurable via a --delay CLI flag 
   (default 1.0 seconds).

5. Wrap response.json() calls in try/except to catch malformed JSON 
   responses and return a graceful error record instead of crashing, 
   consistent with how requests.RequestException is already handled.

6. Move CONTRA_COSTA_CITY_CODES into a JSON config file (similar to 
   contra_costa_targets.json) so city coverage can expand without code 
   changes.

7. Add requirements-dev.txt with pytest and pyshp, and add a README note 
   on how to run tests.

8. Add test coverage for: malformed JSON handling in the property-search 
   path (before removal, or skip if removed in step 1), and 
   save_to_database's upsert behavior when the same parcel appears twice 
   in one run.

After each change, run the existing test suite (pytest scraper/tests 
prospect_model/tests) and fix any breakage before moving to the next item.
```

## Notes on using this

- **Item 1 is the one to do first and review separately** — it changes
  behavior (removing a data source), not just code structure, so review
  that diff carefully before merging.
- Items 2–8 are safe refactors/additions that shouldn't change behavior,
  but a passing test suite after each step is your safety net.
- If you're running this in Claude Code, it can execute the tests directly
  since it has real project and network access.
