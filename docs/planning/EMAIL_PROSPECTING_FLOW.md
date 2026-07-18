# eastbayrealestate — Email Prospecting Flow (Architecture)

## Important starting constraint

`scraper/SOURCE_POLICY.md` currently and deliberately **prohibits
collecting email addresses** — the scraper only gathers property/parcel
facts and, in narrow approved cases, a publicly displayed name. That means
this system does not produce email addresses on its own, and it shouldn't
start scraping for them: an email address paired with a specific person is
exactly the kind of personal contact data the project has intentionally
avoided, and scraping emails from directories, staff pages, or people-search
sites would break both the policy and, likely, the terms of service of
wherever it came from.

So this flow is designed around a **compliant sourcing boundary**: the
scraper produces the *property/owner research*, a human (Deborah) supplies
the *email address* only when she has it through a legitimate channel, and
everything downstream treats that as the entry point.

**Legitimate ways an email enters the system** (all human-sourced, not
scraped):
- A referral or introduction (attorney, past client, mutual contact)
- The owner's own publicly listed business/professional email, only where
  a target already has `allow_public_contact_names: true` and a human has
  reviewed the source
- An opt-in — the owner contacted Deborah first, or filled out a form
- Deborah's own CRM/contact list from prior relationships

## Compliance layer (non-negotiable)

Any commercial email in the U.S. is governed by the **CAN-SPAM Act**,
regardless of list size or how "warm" the lead is. The flow needs to bake
in, not bolt on:

- Accurate "From," "Reply-To," and subject line (no deception)
- Clear identification that it's a marketing/business message
- A physical postal address in every email (brokerage address works)
- A working, honored opt-out/unsubscribe mechanism
- Opt-outs processed within 10 business days, and no sending to anyone
  who's opted out — ever, even from a new list
- No purchased/harvested lists

Real estate has an added layer: **DNC (Do Not Call) rules apply to phone,
not email**, but MLS and brokerage-specific marketing rules may still
apply — worth a quick check with Deborah's brokerage compliance contact
before the first real send.

## Flow overview

```
[Scraper/prospect_model output]          [Human-sourced email, when Deborah has one]
        |                                              |
        v                                              v
   leads (SQLite)  ---------- lead_id ----------> outreach_contacts (new table)
        |                                              |
        v                                              v
  review_status = 'approved'   <----loop-----   Deborah confirms she has
        |                                        a legitimate, compliant
        |                                        email source for this lead
        v
  Segment & assign to a sequence
        |
        v
  Personalized template rendered
        |
        v
  Send via email service (not the scraper) --> outreach_events (already exists)
        |
        v
  Track opens/replies/opt-outs --> feed back into lead_rating / review
```

## 1. Data model additions

The `outreach_events` table already exists in
`prospect_model/score_prospects.py` — it's built for exactly this. Add one
new table to hold the email itself and its provenance, kept deliberately
separate from `leads` so a missing/removed email doesn't require touching
the property record:

```sql
CREATE TABLE outreach_contacts (
    id INTEGER PRIMARY KEY,
    lead_id INTEGER NOT NULL REFERENCES leads(id),
    email TEXT NOT NULL,
    source TEXT NOT NULL,           -- 'referral', 'public_listing', 'opt_in', 'existing_relationship'
    source_notes TEXT,              -- how/where Deborah got it
    added_by TEXT NOT NULL,         -- who confirmed this is legitimate
    added_at TEXT NOT NULL,
    consent_basis TEXT NOT NULL,    -- short human note on why sending is appropriate
    opted_out INTEGER NOT NULL DEFAULT 0,
    opted_out_at TEXT,
    UNIQUE(lead_id, email)
);
```

A row only gets created when a human explicitly adds it — there is no
automated path that populates this table. `opted_out` is checked before
every single send, permanently, regardless of what sequence or list is
being used.

## 2. Segmentation

Use what's already being computed rather than inventing new categories:

- **`lead_rating` / `tier`** (A/B/C/D from the scraper, or
  `high_review_priority` / `review_priority` from `prospect_model`) —
  controls how much personalization effort a sequence gets.
- **`prospect_type`** (`property_record`, `permit_signal`, `probate` once
  that's built, etc.) — controls which template/sequence applies, since a
  permit-signal lead and a probate-estate contact need very different
  tone and content.
- **`relocation_signal` / new relocation features** — a genuinely
  relocation-flagged property gets different messaging than a cold
  property-record lead.
- **Area** (once `--area` filtering from the earlier improvement lands) —
  lets Deborah run area-specific campaigns (e.g. a Danville-specific note
  about the local market).

## 3. Sequence design

Keep sequences short and property-specific rather than generic drip blasts
— this matches the project's existing "reviewable, defensible, arm's-length"
posture:

| Step | Timing | Content focus |
|---|---|---|
| 1 | Day 0 | Specific, factual reason for reaching out (e.g. permit activity, recent market context for their area) — not generic "thinking of selling?" copy |
| 2 | Day 5–7 | Value-add: local market data, a relevant comp, or an answer to something implied by step 1 |
| 3 | Day 14 | Soft, low-pressure close — offer a no-obligation conversation, easy opt-out reminder |

Stop the sequence automatically on: reply, opt-out, or `review_status`
being reverted (e.g. if the lead turns out to be inaccurate on manual
re-check).

## 4. Template & personalization

Each template should pull directly from the lead record so messages read
as researched, not mass-produced:
- Property address / area
- The specific `lead_reason` (e.g. "recent building permit activity" —
  phrased naturally, not as raw internal jargon)
- Deborah's own voice — short, factual, no false urgency

Store templates as versioned files (e.g. `outreach/templates/*.md` with
`{{placeholders}}`) so they can be reviewed and edited without touching
code.

## 5. Sending infrastructure

The scraper/database side of this project shouldn't also become an email
sending service — that's a lot of deliverability, authentication (SPF/DKIM/
DMARC), and abuse-prevention infrastructure to maintain well. Better to
generate the personalized content here and hand off to an established
transactional/marketing email provider (e.g. Mailchimp, SendGrid, or
Deborah's brokerage-provided CRM/email tool if it has one) via API or a
simple CSV export — most of these tools already handle unsubscribe links,
suppression lists, and compliance footers correctly out of the box, which
reduces the risk of a hand-rolled sender getting flagged as spam or
missing a legal requirement.

## 6. Tracking & feedback loop

Every send, open, reply, and opt-out gets logged to the existing
`outreach_events` table (`channel = 'email'`). This closes the loop back
to your mother's feedback theme from earlier — actual outreach outcomes
(not just scraped signals) can eventually feed back into refining
`score_feature_row()`'s weights, since you'll have real data on which
signals actually led to conversations.

## 7. Suggested build order

1. Add `outreach_contacts` table + a small CLI/script to add an email with
   its source and consent basis (human-entered only).
2. Add opt-out checking as a hard gate before any send function runs.
3. Build template rendering from lead data (no sending yet — just generate
   the personalized text for Deborah to review/copy).
4. Wire up a real sending provider once templates are reviewed and
   approved, logging every event to `outreach_events`.
5. Build a simple report (CSV or small dashboard) showing sends/opens/
   replies/opt-outs per sequence and per lead source, to inform what's
   actually working.

## Notes

- Steps 1–3 can be built and used entirely manually (Deborah reviews and
  copy/pastes) before any real automated sending exists — that's a
  reasonable place to pause and validate the approach before adding a
  sending provider.
- Worth a short conversation with Deborah's brokerage about any
  brokerage-specific marketing/compliance review process before the first
  real campaign goes out, separate from the CAN-SPAM basics above.
