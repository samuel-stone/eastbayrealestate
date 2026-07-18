#!/usr/bin/env python3
"""Explore how prospect_model/score_prospects.py is scoring the leads database."""
import sqlite3
import sys
from collections import Counter

DB_PATH = "scraper/output/leads.sqlite3"

def main():
    conn = sqlite3.connect(DB_PATH)

    total_leads = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
    print(f"Total leads in database: {total_leads:,}\n")

    # --- Tier breakdown ---
    print("=== Tier breakdown ===")
    tiers = conn.execute("""
        SELECT tier, COUNT(*), MIN(score), MAX(score), AVG(score)
        FROM prospect_scores GROUP BY tier ORDER BY MAX(score) DESC
    """).fetchall()
    for tier, count, lo, hi, avg in tiers:
        pct = 100 * count / total_leads if total_leads else 0
        print(f"  {tier:24s} {count:>8,} leads ({pct:5.1f}%)  score range {lo}-{hi}, avg {avg:.1f}")

    # --- Score distribution ---
    print("\n=== Score distribution ===")
    scores = [row[0] for row in conn.execute("SELECT score FROM prospect_scores").fetchall()]
    score_counts = Counter(scores)
    for score in sorted(score_counts):
        bar = "#" * min(60, score_counts[score] // max(1, total_leads // 2000))
        print(f"  score {score:>3}: {score_counts[score]:>8,}  {bar}")

    # --- Feature completeness: are permit/planning signals ever populated? ---
    print("\n=== Feature completeness (is real permit/planning data flowing in?) ===")
    feature_stats = conn.execute("""
        SELECT
            SUM(CASE WHEN verified_parcel = 1 THEN 1 ELSE 0 END) AS has_parcel,
            SUM(CASE WHEN building_permit_count_24m > 0 THEN 1 ELSE 0 END) AS has_permits,
            SUM(CASE WHEN planning_application_count_24m > 0 THEN 1 ELSE 0 END) AS has_planning,
            SUM(CASE WHEN major_project_type IS NOT NULL AND major_project_type != '' THEN 1 ELSE 0 END) AS has_project_type,
            COUNT(*) AS total
        FROM prospect_features
    """).fetchone()
    has_parcel, has_permits, has_planning, has_project_type, total = feature_stats
    print(f"  verified_parcel populated:        {has_parcel:,} / {total:,}")
    print(f"  building_permit_count_24m > 0:    {has_permits:,} / {total:,}")
    print(f"  planning_application_count_24m>0: {has_planning:,} / {total:,}")
    print(f"  major_project_type populated:     {has_project_type:,} / {total:,}")

    # --- Sample of the highest-scoring leads, with their reasons ---
    print("\n=== Top 10 highest-scoring leads ===")
    top = conn.execute("""
        SELECT l.address, l.city, ps.score, ps.tier, ps.reasons
        FROM prospect_scores ps
        JOIN leads l ON l.id = ps.lead_id
        ORDER BY ps.score DESC
        LIMIT 10
    """).fetchall()
    for address, city, score, tier, reasons in top:
        print(f"  [{score:>3}] {tier:22s} {address}, {city}  -- {reasons}")

    conn.close()

if __name__ == "__main__":
    main()