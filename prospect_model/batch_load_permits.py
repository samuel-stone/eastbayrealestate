import os
import glob
import sqlite3
import json
from datetime import datetime
from extract_weekly_permits import extract_permit_data

DB_PATH = 'scraper/output/leads.sqlite3'
LEADS_APN_COLUMN = 'parcel_number'

def batch_process():
    pdf_files = glob.glob('permit_pdfs/*.pdf')
    print(f"Found {len(pdf_files)} PDFs to process.")
    
    # 1. Load the database map ONCE for the entire batch
    print("Mapping database APNs into memory ONCE...")
    apn_to_lead_id = {}
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT id, {LEADS_APN_COLUMN} FROM leads WHERE {LEADS_APN_COLUMN} IS NOT NULL")
        for lead_id, parcel in cursor.fetchall():
            clean_parcel = str(parcel).replace('-', '').strip()
            apn_to_lead_id[clean_parcel] = lead_id

    # 2. Process all PDFs
    total_success = 0
    updated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    sources_json = json.dumps(["county_weekly_archive"])
    
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        for file_path in pdf_files:
            print(f"\nProcessing {os.path.basename(file_path)}...")
            try:
                # Reuse your existing parser
                df = extract_permit_data(file_path)
                if df.empty:
                    continue
                    
                df.columns = [col.lower().strip() for col in df.columns]
                if 'apn' not in df.columns:
                    print(" -> No 'apn' column found, skipping.")
                    continue

                df['apn_clean'] = df['apn'].astype(str).str.replace('-', '', regex=False).str.strip()
                df = df[df['apn_clean'].str.len() >= 9].copy()
                
                if 'description' not in df.columns:
                    df['description'] = ""
                major_keywords = 'adu|addition|subdivision|demolition|new construction'
                df['is_major_project'] = df['description'].str.contains(major_keywords, case=False, na=False)
                
                file_success = 0
                for _, row in df.iterrows():
                    apn = row['apn_clean']
                    if apn not in apn_to_lead_id:
                        continue
                        
                    target_lead_id = apn_to_lead_id[apn]
                    has_major = bool(row.get('is_major_project', False))
                    major_proj = row['description'] if has_major else None
                    
                    # LOGGING LOGIC: Persist raw description for semantic analysis
                    cursor.execute("""
                        INSERT INTO permit_details (lead_id, description, permit_type, date_processed)
                        VALUES (?, ?, ?, ?)
                    """, (target_lead_id, row.get('description', ''), row.get('type', 'Unknown'), datetime.now().isoformat()))
                    
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
                    
                    file_success += 1
                    total_success += 1
                    
                print(f" -> Matched {file_success} properties.")
            except Exception as e:
                print(f" -> Error parsing {file_path}: {e}")
                
        # Commit all database changes at the very end
        conn.commit()
        print(f"\n=== BATCH COMPLETE ===")
        print(f"Successfully updated {total_success} total records across {len(pdf_files)} PDFs.")

if __name__ == "__main__":
    batch_process()