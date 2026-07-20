# East Bay Real Estate Automation - Scraper & Infrastructure Patch Log

Last Updated: 2026-07-19

Purpose:
This document tracks known bugs, fixes, tests, and deployment issues discovered while building the scraper, automation engine, and Railway worker/agent/scheduler pipeline.

These fixes are intentionally staged. Do not patch everything at once. Stabilize the pipeline first, then harden scrapers.

---

# 1. Walnut Creek Permit Loader Database Constraint Failure

## Symptom

Running:

```bash
python3 load_walnut_creek_permits.py