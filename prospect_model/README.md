# Property prospect model

This folder develops a transparent, public-record **research-priority** score for Deb Stone's real-estate prospecting. It does not predict an individual's intent, eligibility, financial capacity, or likelihood of responding.

## What the score means

The score answers: **which properties have the strongest, recent, verifiable public property activity worth a human review?** A high score is never permission to contact someone automatically.

The baseline score is explainable and property-based:

| Signal | Maximum points | Evidence |
| --- | ---: | --- |
| Recent completed building permit | 35 | Official permit record and date |
| Recent planning/land-use application | 30 | Official planning record and date |
| Recent major project signal (ADU, addition, subdivision, demolition) | 20 | Official project type |
| Verified parcel/APN and address | 10 | County parcel download |
| Fresh source observation | 5 | Public-source timestamp |

No protected traits, people-search data, contact details, household data, or demographic proxies may be used as features.

## Data sources to add in priority order

1. **Contra Costa parcel download** — already loaded; address/APN identity and source freshness.
2. **County and city permit/planning records** — record number, address/APN, status, project type, and public dates. The County's permit system covers unincorporated areas and certain contract cities; each city needs its own source adapter where it operates a separate system.
3. **Public planning agendas, staff reports, and project lists** — public hearing/project activity that can be joined to an address/APN.
4. **County planning/GIS layers** — zoning, land-use designation, city jurisdiction, and publicly published development layers; use these as property context, not people-based targeting.
5. **Aggregate market context** — monthly city/neighborhood-level inventory, days on market, and price trends from a licensed source or an openly licensed aggregate dataset. Keep it geography-level and never use demographics to prioritize individual properties.
6. **Public hazard/context layers** — only for service content or advisory relevance after brokerage review, never as a reason to exclude people or neighborhoods from outreach.

Do not scrape listing portals, social networks, people-search sites, gated systems, or any site whose terms do not permit the collection. Do not use race, religion, national origin, sex, disability, familial status, age, income, credit, household composition, language, or geographic proxies for these characteristics.

## Database tables

`score_prospects.py` creates the following tables inside `scraper/output/leads.sqlite3`:

- `prospect_features`: source-specific property features and their observed dates.
- `prospect_scores`: current score, tier, reasons, version, and calculated time.
- `outreach_events`: human-recorded, consent-aware outreach history.

## Run the baseline scorer

From the project root:

```bash
python3 prospect_model/score_prospects.py --database scraper/output/leads.sqlite3
```

With today's parcel-only dataset, every property receives a small data-readiness score and an `insufficient_evidence` tier. That is expected. Scores become useful after permitted/official permit and planning adapters populate `prospect_features`.

## Outreach approach

Start with a geographic, property-neutral direct-mail test: one or two carrier routes near a verified public activity cluster. A short postcard should offer useful local information—such as an ADU/remodel resale guide, neighborhood market update, or a no-pressure value review—plus a clear response path and broker/license information.

USPS Every Door Direct Mail can deliver to every active address on a selected carrier route without purchasing a name/address list. This is the recommended first outbound channel because the parcel dataset has property addresses but no owner names. Keep an outreach log and honor suppression requests. Do not call/text unless the brokerage's compliance process has approved the contact source and required suppression/consent checks.

## Before deployment

- Have Compass/brokerage compliance review the score, source list, creative, and workflow.
- Run a fair-housing impact review whenever adding a new feature or geography rule.
- Audit samples monthly: source accuracy, score reasons, false positives, and outreach outcomes.
- Require a human approval before any outreach event is created.
