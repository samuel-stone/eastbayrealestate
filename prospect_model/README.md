# Property Prospect Model

This project develops a transparent, public-record **research-priority** score for real-estate prospecting. It does not predict an individual's intent, eligibility, financial capacity, or likelihood of responding.

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

## Technical Architecture

The project uses a **cloud-hosted PostgreSQL instance** for all data storage.

### Security
Credentials are kept secure using **macOS Keychain**. To store your database password locally, run:
```bash
security add-generic-password -a "$USER" -s "eastbay-db-password" -w

### Database Tables
leads: Master list of properties and normalized addresses.
permit_details: Granular history of building permits linked to leads.
prospect_features: Consolidated property features and scoring metrics.
adu_targets: Filtered properties identified with ADU/Accessory Dwelling activity.
outreach_events: Human-recorded, consent-aware outreach history.

### Running the Pipeline
Daily Migration & Scoring: Syncs raw permits with lead data and updates prospect scores atomically:

###Bash
python3 -m scripts.load_walnut_creek_permits

Weekly Bulk PDF Extraction: Parses county reports and performs high-speed bulk updates:

###Bash
python3 -m prospect_model.extract_weekly_permits <path_to_pdf>

## Outreach Approach
Compliance: Review scores, sources, and creative with brokerage compliance.
Audit: Audit samples monthly for source accuracy and false positives.
Approval: Human approval is required before any outreach event is created in the database.
