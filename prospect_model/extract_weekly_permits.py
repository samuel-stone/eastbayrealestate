import pandas as pd
import pdfplumber
import re
import os
import keyring
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime

# --- CONFIGURATION ---
PASSWORD = keyring.get_password("eastbay-db-password", os.environ.get("USER"))
DATABASE_URL = f"postgres://avnadmin:{PASSWORD}@pg-305dd876-eastbayrealestate.l.aivencloud.com:22742/defaultdb?sslmode=require"

def extract_permit_data(file_path):
    all_records = []
    # Simplified regex for robustness
    line_pattern = re.compile(r"^([A-Z0-9]+-\d+)\s+[A-Z]+\s+[A-Za-z]+\s+\d{1,2}/\d{1,2}/\d{4}\s+\$[\d,]+\.\d{2}\s+(.*?)\s+(?:\d+\s+)?(\d{9})\s+(.*)")

    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text: continue
            for line in text.split('\n'):
                match = line_pattern.match(line.strip())
                if match:
                    all_records.append({
                        'permit_no': match.group(1),
                        'description': match.group(2).strip(),
                        'apn': match.group(3).strip()
                    })
    return pd.DataFrame(all_records)

def load_to_database_bulk(df):
    if df.empty: return

    # 1. Connect to PostgreSQL
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    try:
        # 2. Get Lead Mappings in one query
        cursor.execute("SELECT id, REPLACE(parcel_number, '-', '') FROM leads WHERE parcel_number IS NOT NULL")
        apn_map = {str(apn): lead_id for lead_id, apn in cursor.fetchall()}

        # 3. Prepare data for bulk update
        # We only keep rows that exist in our leads database
        df['lead_id'] = df['apn'].map(apn_map)
        df_valid = df.dropna(subset=['lead_id']).copy()

        print(f"Bulk updating {len(df_valid)} records...")

        # 4. Use a Temporary Table for high-speed batch processing
        cursor.execute("CREATE TEMP TABLE tmp_permits (lead_id INT, desc_text TEXT);")
        execute_values(cursor, "INSERT INTO tmp_permits VALUES %s", df_valid[['lead_id', 'description']].values)

        # 5. Perform a Single Set-Based Update
        cursor.execute("""
            UPDATE prospect_features pf
            SET 
                building_permit_count_24m = pf.building_permit_count_24m + 1,
                fresh_observation = 1,
                updated_at = NOW()
            FROM tmp_permits t
            WHERE pf.lead_id = t.lead_id;
        """)
        
        conn.commit()
        print("Bulk update successful.")
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    import sys
    file = sys.argv[1] if len(sys.argv) > 1 else "permit_report.pdf"
    df = extract_permit_data(file)
    load_to_database_bulk(df)