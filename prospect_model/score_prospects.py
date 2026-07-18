#!/usr/bin/env python3
"""Transparent public-record property research-priority scorer."""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

SCORE_VERSION = "public_record_v0.1"


def score_feature_row(feature: dict[str, object]) -> tuple[int, list[str]]:
    """Score only explicit, property-level public-record evidence."""
    score = 0
    reasons: list[str] = []

    if feature.get("verified_parcel"):
        score += 10
        reasons.append("verified parcel")
    if feature.get("fresh_observation"):
        score += 5
        reasons.append("current public-source observation")

    permits = min(int(feature.get("building_permit_count_24m", 0) or 0), 3)
    if permits:
        score += min(35, permits * 15)
        reasons.append(f"{permits} recent building permit(s)")

    planning = min(int(feature.get("planning_application_count_24m", 0) or 0), 2)
    if planning:
        score += min(30, planning * 20)
        reasons.append(f"{planning} recent planning application(s)")

    if feature.get("major_project_type"):
        score += 20
        reasons.append(f"public project: {feature['major_project_type']}")

    return min(score, 100), reasons


def tier_for_score(score: int) -> str:
    if score >= 60:
        return "high_review_priority"
    if score >= 30:
        return "review_priority"
    return "insufficient_evidence"


def ensure_tables(connection: sqlite3.Connection) -> None:
    connection.executescript("""
        CREATE TABLE IF NOT EXISTS prospect_features (
            lead_id INTEGER PRIMARY KEY REFERENCES leads(id),
            verified_parcel INTEGER NOT NULL DEFAULT 0,
            fresh_observation INTEGER NOT NULL DEFAULT 0,
            building_permit_count_24m INTEGER NOT NULL DEFAULT 0,
            planning_application_count_24m INTEGER NOT NULL DEFAULT 0,
            major_project_type TEXT,
            feature_source_urls TEXT NOT NULL DEFAULT '[]',
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS prospect_scores (
            lead_id INTEGER PRIMARY KEY REFERENCES leads(id),
            score INTEGER NOT NULL,
            tier TEXT NOT NULL,
            reasons TEXT NOT NULL,
            score_version TEXT NOT NULL,
            calculated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS outreach_events (
            id INTEGER PRIMARY KEY,
            lead_id INTEGER NOT NULL REFERENCES leads(id),
            channel TEXT NOT NULL,
            event_type TEXT NOT NULL,
            occurred_at TEXT NOT NULL,
            approved_by TEXT NOT NULL,
            notes TEXT,
            UNIQUE(lead_id, channel, event_type, occurred_at)
        );
    """)


def seed_parcel_features(connection: sqlite3.Connection, timestamp: str) -> None:
    connection.execute("""
        INSERT OR IGNORE INTO prospect_features (lead_id, verified_parcel, fresh_observation, updated_at)
        SELECT id,
               CASE WHEN parcel_number <> '' THEN 1 ELSE 0 END,
               1,
               ?
        FROM leads
    """, (timestamp,))
    connection.execute("""
        UPDATE prospect_features
        SET verified_parcel = COALESCE((
                SELECT CASE WHEN leads.parcel_number <> '' THEN 1 ELSE 0 END
                FROM leads
                WHERE leads.id = prospect_features.lead_id
            ), 0),
            fresh_observation = 1,
            updated_at = ?
        WHERE lead_id IN (SELECT id FROM leads)
    """, (timestamp,))


def score_database(database_path: str) -> int:
    database = Path(database_path)
    if not database.exists():
        raise SystemExit(f"Lead database does not exist: {database}")

    timestamp = datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(database) as connection:
        ensure_tables(connection)
        seed_parcel_features(connection, timestamp)
        feature_rows = connection.execute("""
            SELECT lead_id, verified_parcel, fresh_observation,
                   building_permit_count_24m, planning_application_count_24m,
                   major_project_type
            FROM prospect_features
        """).fetchall()
        for row in feature_rows:
            feature = {
                "verified_parcel": row[1],
                "fresh_observation": row[2],
                "building_permit_count_24m": row[3],
                "planning_application_count_24m": row[4],
                "major_project_type": row[5],
            }
            score, reasons = score_feature_row(feature)
            connection.execute("""
                INSERT INTO prospect_scores (lead_id, score, tier, reasons, score_version, calculated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(lead_id) DO UPDATE SET
                    score = excluded.score,
                    tier = excluded.tier,
                    reasons = excluded.reasons,
                    score_version = excluded.score_version,
                    calculated_at = excluded.calculated_at
            """, (row[0], score, tier_for_score(score), json.dumps(reasons), SCORE_VERSION, timestamp))
    return len(feature_rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", default="scraper/output/leads.sqlite3")
    args = parser.parse_args()
    count = score_database(args.database)
    print(f"Scored {count:,} leads using {SCORE_VERSION}")


if __name__ == "__main__":
    main()
