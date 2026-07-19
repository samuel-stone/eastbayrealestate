"""
run_reports.py — rewritten to use Aiven Postgres (via DATABASE_URL) instead of
the old local scraper/output/leads.sqlite3 file, which doesn't exist in the
Railway container and caused:
    sqlite3.OperationalError: unable to open database file

Since there's no S3/file storage set up yet, results are written into a
`reports` table in Postgres instead of local CSV files (which would vanish
on container restart anyway). Add S3/CSV export later if needed.

KNOWN CAVEATS (please review):
1. `prospect_features` (verified_parcel, building_permit_count_24m,
   planning_application_count_24m, major_project_type) is currently EMPTY
   for all 6,932 rows -- confirmed via direct query on 2026-07-19. So
   `priority_prospects` below is built from `permit_details.permit_type`
   instead (which IS populated), filtering for keywords that signal real
   project activity (new construction, additions, alterations, revisions).
   Revisit this once prospect_features enrichment is actually populated.
2. `permit_details.date_processed` is a TEXT column populated with
   `datetime.now()` at *migration/load* time (see load_walnut_creek_permits.py),
   not the actual permit issue date. So "active in the last 90 days" reflects
   when data was loaded into the DB, not necessarily recent real-world permit
   activity. `issued_date` would be the more meaningful field once its
   population is fixed (see BUGFIX_LOG.md item on column-name mismatch).
"""
import os
import json
from datetime import datetime, timezone

import psycopg2
import psycopg2.extras


def get_db_connection():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL environment variable is not set!")
    return psycopg2.connect(db_url, sslmode="require")


REPORTS = {
    "developer_whales": """
        SELECT l.address, COUNT(*) AS project_count
        FROM leads l
        JOIN permit_details pd ON l.id = pd.lead_id
        GROUP BY l.id, l.address
        HAVING COUNT(*) > 1
        ORDER BY project_count DESC;
    """,
    "active_velocity": """
        SELECT l.address, COUNT(*) AS recent_permits
        FROM leads l
        JOIN permit_details pd ON l.id = pd.lead_id
        WHERE pd.date_processed::timestamptz > NOW() - INTERVAL '90 days'
        GROUP BY l.id, l.address
        HAVING COUNT(*) > 1
        ORDER BY recent_permits DESC;
    """,
    "priority_prospects": """
        SELECT
            l.address,
            l.contact_name,
            STRING_AGG(DISTINCT pd.permit_type, ' | ') AS intent_categories,
            STRING_AGG(DISTINCT pd.description, ' | ') AS all_permit_descriptions
        FROM leads l
        JOIN permit_details pd ON l.id = pd.lead_id
        WHERE pd.permit_type ILIKE '%%New Construction%%'
           OR pd.permit_type ILIKE '%%Addition%%'
           OR pd.permit_type ILIKE '%%Alteration%%'
           OR pd.permit_type ILIKE '%%Revision%%'
        GROUP BY l.id, l.address, l.contact_name;
    """,
}


def ensure_reports_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id SERIAL PRIMARY KEY,
            report_name TEXT NOT NULL,
            generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            row_count INTEGER NOT NULL,
            rows JSONB NOT NULL
        );
    """)


def generate_reports():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    try:
        ensure_reports_table(cursor)
        conn.commit()

        for report_name, query in REPORTS.items():
            try:
                cursor.execute(query)
                rows = cursor.fetchall()

                rows_as_dicts = [dict(row) for row in rows]
                rows_json = json.dumps(rows_as_dicts, default=str)

                cursor.execute(
                    """
                    INSERT INTO reports (report_name, generated_at, row_count, rows)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (report_name, datetime.now(timezone.utc), len(rows_as_dicts), rows_json),
                )
                conn.commit()

                print(f"Generated: {report_name} ({len(rows_as_dicts)} rows) -> saved to reports table")

            except Exception as e:
                conn.rollback()
                print(f"Error generating {report_name}: {e}")

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    generate_reports()