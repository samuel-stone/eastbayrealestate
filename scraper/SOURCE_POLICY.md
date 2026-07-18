# Public-source lead policy

This tool creates a **review queue**, not an automatic outreach list. Every exported row must keep its source URL and scrape timestamp.

## Allowed collection

- Address, city, APN/parcel number, publicly displayed assessed value, permit/planning activity, and the public source URL.
- A name only when it is displayed as a property owner, applicant, or project contact on an official public record and the target has `allow_public_contact_names: true`.

## Do not collect

- Phone numbers, email addresses, social profile details, household-member information, or any information from a login, payment, CAPTCHA, or restricted portal.
- Names from general web pages, staff directories, people-search sites, or inferred matches.

## Source approval

Keep `allow_public_contact_names` set to `false` until a person reviews the source's access rules and confirms that the particular record type is public and suitable for this limited use. The Contra Costa County Assessor's online property tools do not display owner names, so they are address/parcel sources only.

## Before outreach

1. Verify the address and signal against the recorded URL.
2. Confirm the record is current and does not contain a protected or sensitive indicator.
3. Review the intended outreach against applicable brokerage, local, state, and federal marketing rules.
