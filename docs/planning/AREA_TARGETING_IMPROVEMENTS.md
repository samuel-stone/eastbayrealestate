# eastbayrealestate — Area Targeting Improvements

Based on feedback from Deborah (the agent): results should be filterable
by specific target areas — starting with Rossmoor, Danville, Alamo, and
Walnut Creek. This is a real expansion, not just config changes:

- **Rossmoor** is an unincorporated senior community inside Walnut Creek's
  zip codes (94595, 94596) — it has no separate "city" value in property
  records, so it can only be targeted by zip code, not city name.
- **Danville** and **Alamo** are in Contra Costa County (San Ramon Valley
  area) but are not yet in the scraper's city list at all.

Use this as a prompt for Claude Code (or any coding assistant with repo
access) to implement the change. Run the test suite after each numbered
item.

```
I want to add area-based filtering to the eastbayrealestate scraper so 
leads can be targeted to specific neighborhoods/cities, including areas 
that are only identifiable by zip code (like Rossmoor). Please make the 
following changes, testing as you go:

1. Create a new config file, scraper/target_areas.json, defining named 
   areas with the cities and/or zip codes that belong to them:

   {
     "areas": {
       "walnut_creek": {
         "cities": ["WALNUT CREEK"],
         "zips": ["94595", "94596", "94597", "94598"]
       },
       "rossmoor": {
         "cities": [],
         "zips": ["94595", "94596"],
         "notes": "Unincorporated senior community inside Walnut Creek zip 
                   codes; has no separate city value in property records, 
                   so must be matched by zip only. Note this zip range 
                   overlaps with Walnut Creek generally -- see step 4 for 
                   how to disambiguate."
       },
       "danville": {
         "cities": ["DANVILLE"],
         "zips": ["94506", "94526"]
       },
       "alamo": {
         "cities": ["ALAMO"],
         "zips": ["94507"]
       }
     }
   }

   Confirm the exact zip codes and any Rossmoor-specific parcel/street 
   identifiers (e.g. street name patterns or a subdivision code, if the 
   Contra Costa parcel data exposes one) before finalizing -- flag this 
   for a human to verify rather than guessing silently.

2. Add zip code as a recognized field. Check whether the Contra Costa 
   parcel shapefile schema includes a zip/postal field (e.g. SITUS_ZIP, 
   ZIP, ZIPCODE). If so, extend select_first_field's candidate list and 
   capture zip in the parcel-derived records the same way address/city 
   are captured. If the current data source does NOT expose zip codes, 
   flag this clearly -- we may need a different official data source or 
   a zip-lookup step for Rossmoor specifically, since it can't be 
   identified any other way.

3. Extend the existing matching_city() logic (or add a new matching_area() 
   function) so records can be filtered against a named area from 
   target_areas.json: match on city name OR zip code, since some areas 
   (like Rossmoor) are zip-only.

4. Handle the Rossmoor/Walnut Creek zip overlap explicitly: since 
   Rossmoor's zip codes are shared with broader Walnut Creek, matching 
   zip alone isn't precise enough to separate the two. Investigate 
   whether the parcel data has a subdivision name, community name, or 
   street-level pattern that identifies Rossmoor specifically (Rossmoor 
   is a gated community with a distinct, known street list) and use that 
   for disambiguation. If no reliable signal exists in the current data 
   source, document this limitation clearly in scraper/README.md rather 
   than silently over- or under-including Rossmoor parcels.

5. Add a `--area` CLI flag to scraper/scrape_public_data.py (e.g. 
   --area rossmoor, --area danville) that filters the final output to 
   only that named area, using target_areas.json. Keep the existing 
   --parcel-cities flag working as-is for ad hoc filtering, but --area 
   should be the primary, documented way to target these named areas 
   going forward. Support comma-separated multiple areas 
   (--area rossmoor,danville).

6. Update scraper/README.md with a short section on how to use --area, 
   listing the currently supported named areas.

7. Add test coverage for: matching_area() with a zip-only area (Rossmoor), 
   a city-only area, an area with both, and the CLI flag itself filtering 
   correctly when given multiple areas.

After each change, run the existing test suite (pytest scraper/tests 
prospect_model/tests) and fix any breakage before moving to the next item.
```

## Notes on using this

- **Step 4 is the one to review carefully.** Rossmoor can't be reliably
  separated from the rest of Walnut Creek by zip code alone, and it's
  better for the coding assistant to surface that limitation than to
  quietly produce a filter that's wrong. If it turns out there's no clean
  way to isolate Rossmoor parcels from the current data source, the
  practical fallback is exporting all Walnut Creek/94595-94596 results
  and reviewing manually until a better identifier is found (e.g. a
  known Rossmoor street list).
- Once this lands, running the scraper with `--area rossmoor` (or
  `danville`, `alamo`, `walnut_creek`) should produce one filtered CSV
  for that area, per your preference for a single file with an area
  filter flag rather than separate files per area.
