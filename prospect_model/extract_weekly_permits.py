import sqlite3
import pandas as pd
import pdfplumber
import json
import re
from datetime import datetime

# Database configuration
DB_PATH = 'scraper/output/leads.sqlite3'
LEADS_APN_COLUMN = 'parcel_number'

def extract_permit_data(file_path):
    all_records = []
    current_record = None

    # Regex to match the main permit line
    line_pattern = re.compile(
        r"^([A-Z0-9]+-\d+)\s+"        # Permit Number
        r"[A-Z]+\s+"                  # Type
        r"([A-Za-z]+)\s+"             # Status
        r"(\d{1,2}/\d{1,2}/\d{4})\s+" # Date
        r"\$[\d,]+\.\d{2}\s+"         # Valuation
        r"(.*?)\s+"                   # Description (start)
        r"(?:\d+\s+)?"                # Optional SQ FT
        r"(\d{9})\s+"                 # APN
        r"(.*)"                       # Address/Contractor
    )

    print(f"Parsing PDF: {file_path}...")
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
                
            for line in text.split('\n'):
                match = line_pattern.match(line)
                
                if match:
                    if current_record:
                        all_records.append(current_record)
                        
                    current_record = {
                        'permit_number': match.group(1),
                        'status': match.group(2),
                        'issued_date': match.group(3),
                        'description': match.group(4).strip(),
                        'apn': match.group(5)
                    }
                else:
                    ignore_phrases = ['Contra Costa', 'Building Permits', 'Issued Between', 'City:', 'PERMIT NUMBER']
                    if current_record and line.strip() and not any(line.startswith(p) for p in ignore_phrases):
                        current_record['description'] += " " + line.strip()
                        
    if current_record:
        all_records.append(current_record)
        
    df = pd.DataFrame(all_records)
    print(f"Successfully parsed {len(df)} permits from the PDF.")
    return df

def load_to_database(df, db_path):
    if df.empty:
        print("No records found in PDF to load.")
        return

    df.columns = [col.lower().strip() for col in df.columns]
    df['apn_clean'] = df['apn'].astype(str).str.replace('-', '', regex=False).str.strip()
    df = df[df['apn_clean'].str.len() >= 9].copy()
    
    major_keywords = 'adu|addition|subdivision|demolition|new construction'
    df['is_major_project'] = df['description'].str.contains(major_keywords, case=False, na=False)

    updated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    sources_json = json.dumps(["county_weekly_report"])
    
    success_count = 0
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            print("Mapping database APNs into memory for fast matching...")
            # Fetch all APNs once (O(1) lookup in memory)
            cursor.execute(f"SELECT id, {LEADS_APN_COLUMN} FROM leads WHERE {LEADS_APN_COLUMN} IS NOT NULL")
            apn_to_lead_id = {}
            for lead_id, parcel in cursor.fetchall():
                clean_parcel = str(parcel).replace('-', '').strip()
                apn_to_lead_id[clean_parcel] = lead_id
            
            print("Running rapid database updates...")
            for _, row in df.iterrows():
                apn = row['apn_clean']
                
                # Skip if this permit's APN isn't in our leads database
                if apn not in apn_to_lead_id:
                    continue
                    
                target_lead_id = apn_to_lead_id[apn]
                has_major = bool(row['is_major_project'])
                major_proj = row['description'] if has_major else None
                
                # Update by strict lead_id (Instant execution)
                if has_major:
                    update_sql = """
                        UPDATE prospect_features
                        SET 
                            building_permit_count_24m = building_permit_count_24m + 1,
                            major_project_type = CASE 
                                WHEN major_project_type IS NULL THEN ? 
                                ELSE major_project_type || '; ' || ? 
                            END,
                            fresh_observation = 1,
                            feature_source_urls = ?,
                            updated_at = ?
                        WHERE lead_id = ?
                    """
                    cursor.execute(update_sql, (major_proj, major_proj, sources_json, updated_at, target_lead_id))
                else:
                    update_sql = """
                        UPDATE prospect_features
                        SET 
                            building_permit_count_24m = building_permit_count_24m + 1,
                            fresh_observation = 1,
                            feature_source_urls = ?,
                            updated_at = ?
                        WHERE lead_id = ?
                    """
                    cursor.execute(update_sql, (sources_json, updated_at, target_lead_id))
                
                success_count += 1
                    
            conn.commit()
            print(f"Pipeline executed. Successfully updated {success_count} matching records in the database.")
            
    except sqlite3.Error as e:
        print(f"Database error: {e}")

if __name__ == "__main__":
    print("Starting weekly permit extraction pipeline...")
    raw_df = extract_permit_data("permit_report.pdf")
    load_to_database(raw_df, DB_PATH)
    print("Pipeline complete.")

if __name__ == "__main__":
    import sys
    # If a file is passed via the terminal, use it. Otherwise, default to permit_report.pdf
    target_file = sys.argv[1] if len(sys.argv) > 1 else "permit_report.pdf"
    
    print(f"Starting weekly permit extraction pipeline for: {target_file}")
    raw_df = extract_permit_data(target_file)
    load_to_database(raw_df, DB_PATH)
    print("Pipeline complete.")
