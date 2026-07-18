import sqlite3
from datetime import datetime

DB_PATH = 'scraper/output/leads.sqlite3'
SOURCE_TABLE = 'walnut_creek_permits' 

def load_historical_scrape():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        print("Mapping master leads by address...")
        try:
            cursor.execute("SELECT id, UPPER(TRIM(site_address)) FROM leads WHERE site_address IS NOT NULL")
        except sqlite3.OperationalError:
            cursor.execute("SELECT id, UPPER(TRIM(address)) FROM leads WHERE address IS NOT NULL")
            
        address_to_lead_id = {addr: lead_id for lead_id, addr in cursor.fetchall()}
        
        print(f"Fetching Walnut Creek records from {SOURCE_TABLE}...")
        cursor.execute(f"SELECT * FROM {SOURCE_TABLE}")
        columns = [desc[0] for desc in cursor.description]
        wc_records = cursor.fetchall()
        
        col_map = {col: idx for idx, col in enumerate(columns)}
        matched = inserted = 0
        
        print("Migrating records into permit_details...")
        for row in wc_records:
            address = row[col_map.get('address', -1)] if 'address' in col_map else ""
            permit_no = row[col_map.get('permit_no', -1)] if 'permit_no' in col_map else f"WC-MIGRATE-{matched}"
            permit_date = row[col_map.get('permit_date', -1)] if 'permit_date' in col_map else None
            permit_type = row[col_map.get('permit_type', -1)] if 'permit_type' in col_map else "Unknown"
            description = row[col_map.get('description', -1)] if 'description' in col_map else ""
            
            if not address:
                continue
                
            # THE FIX: Split at the first comma to isolate just the street address
            clean_address = str(address).upper().split(',')[0].strip()
            
            lead_id = address_to_lead_id.get(clean_address)
            if not lead_id:
                continue
                
            matched += 1
            cursor.execute("""
                INSERT OR IGNORE INTO permit_details
                    (lead_id, description, permit_type, date_processed, permit_number, issued_date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (lead_id, description, permit_type, datetime.now().isoformat(), permit_no, permit_date))
            
            if cursor.rowcount:
                inserted += 1
                
        conn.commit()
        print(f"Matched {matched} Walnut Creek addresses to master leads.")
        print(f"Safely inserted {inserted} unique permits into the pipeline.")

if __name__ == "__main__":
    load_historical_scrape()