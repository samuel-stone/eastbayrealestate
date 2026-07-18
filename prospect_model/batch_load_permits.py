"""
Single, canonical entry point for loading parsed permit PDFs into the database.

Replaces the DB-writing logic that used to live in both extract_weekly_permits.py
and this file separately. That duplication -- two independent code paths both
running `building_permit_count_24m = building_permit_count_24m + 1` -- was the
root cause of wildly inflated permit counts. See docs/planning/PERMIT_PIPELINE_FIX.md.

This script now does ONE thing: parse PDFs and store clean, de-duplicated permit
records in `permit_details`. It does NOT touch prospect_features/building_permit_count_24m
directly -- that's computed fresh from permit_details by
prospect_model/compute_permit_features.py.
"""
import os
import sys
import glob
import psycopg2
from db_utils import get_db_connection
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_weekly_permits import extract_permit_data

LEADS_APN_COLUMN = 'parcel_number'


def ensure_schema(conn):
    """Add permit_number/issued_date if this is an older database, and make sure
    the unique index exists so re-processing the same PDF is always a safe no-op."""
    existing_cols = {row[1] for row in conn.execute("PRAGMA table_info(permit_details)").fetchall()}
    if 'permit_number' not in existing_cols:
        conn.execute("ALTER TABLE permit_details ADD COLUMN permit_number TEXT")
    if 'issued_date' not in existing_cols:
        conn.execute("ALTER TABLE permit_details ADD COLUMN issued_date TEXT")
    # NULLs don't collide under a UNIQUE index in SQLite, so this is safe to add
    # even though older rows (from before this fix) won't have a permit_number.
    conn.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_permit_details_permit_number
        ON permit_details(permit_number)
    """)
    conn.commit()


def load_pdf(df, conn, apn_to_lead_id):
    """Insert parsed permit rows for one PDF. Returns (matched_count, inserted_count)."""
    if df.empty:
        return 0, 0

    df = df.copy()
    df['apn_clean'] = df['apn'].astype(str).str.replace('-', '', regex=False).str.strip()
    df = df[df['apn_clean'].str.len() >= 9]

    matched, inserted = 0, 0
    cursor = conn.cursor()
    for _, row in df.iterrows():
        lead_id = apn_to_lead_id.get(row['apn_clean'])
        if lead_id is None:
            continue
        matched += 1
        cursor.execute("""
            INSERT OR IGNORE INTO permit_details
                (lead_id, description, permit_type, date_processed, permit_number, issued_date)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            lead_id,
            row.get('description', ''),
            row.get('status', 'Unknown'),
            datetime.now().isoformat(),
            row.get('permit_number'),
            row.get('issued_date'),
        ))
        if cursor.rowcount:  # 0 if INSERT OR IGNORE skipped a duplicate permit_number
            inserted += 1
    return matched, inserted


def batch_process(target=None):
    pdf_files = [target] if target else glob.glob('permit_pdfs/*.pdf')
    print(f"Found {len(pdf_files)} PDF(s) to process.")

    with get_db_connection() as conn:
        ensure_schema(conn)

        print("Mapping database APNs into memory...")
        cursor = conn.cursor()
        
        # Querying the restored master leads table
        cursor.execute(f"SELECT id, {LEADS_APN_COLUMN} FROM leads WHERE {LEADS_APN_COLUMN} IS NOT NULL")
        apn_to_lead_id = {
            str(parcel).replace('-', '').strip(): lead_id
            for lead_id, parcel in cursor.fetchall()
        }

        total_matched, total_inserted = 0, 0
        for file_path in pdf_files:
            print(f"\nProcessing {os.path.basename(file_path)}...")
            try:
                df = extract_permit_data(file_path)
                matched, inserted = load_pdf(df, conn, apn_to_lead_id)
                total_matched += matched
                total_inserted += inserted
                skipped = matched - inserted
                print(f" -> Matched {matched} properties. Inserted {inserted} new permits.", end='')
                print(f" Skipped {skipped} already-seen permit numbers." if skipped else "")
            except Exception as e:
                print(f" -> Error parsing {file_path}: {e}")

        conn.commit()

    print(f"\n=== BATCH COMPLETE ===")
    print(f"Matched {total_matched} property references across {len(pdf_files)} PDF(s).")
    print(f"Inserted {total_inserted} new permit records (duplicates were automatically skipped).")
    print(f"\nNext step: run prospect_model/compute_permit_features.py to refresh")
    print(f"building_permit_count_24m and major_project_type from this data.")


if __name__ == "__main__":
    target_file = sys.argv[1] if len(sys.argv) > 1 else None
    batch_process(target_file)