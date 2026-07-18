import sqlite3
import pandas as pd
import os

DB_PATH = 'scraper/output/leads.sqlite3'
REPORT_DIR = 'output/reports'

# The queries are now strictly grouped by lead ID to prevent duplicate addresses in the output CSVs
queries = {
    "developer_whales.csv": """
        SELECT l.address, count(*) as project_count 
        FROM leads l 
        JOIN permit_insights pi ON l.id = pi.lead_id 
        WHERE pi.intent_category = 'Expansion' 
        GROUP BY l.id 
        HAVING project_count > 1 
        ORDER BY project_count DESC;
    """,
    "active_velocity.csv": """
        SELECT l.address, count(*) as recent_permits 
        FROM leads l 
        JOIN permit_details pd ON l.id = pd.lead_id 
        WHERE pd.date_processed > date('now', '-90 days') 
        GROUP BY l.id 
        HAVING recent_permits > 1 
        ORDER BY recent_permits DESC;
    """,
    "priority_prospects.csv": """
        SELECT 
            l.address, 
            l.contact_name, 
            GROUP_CONCAT(DISTINCT pi.intent_category) as intent_categories, 
            GROUP_CONCAT(pi.description, ' | ') as all_permit_descriptions 
        FROM leads l 
        JOIN permit_insights pi ON l.id = pi.lead_id 
        WHERE pi.intent_category IN ('Expansion', 'Renovation')
        GROUP BY l.id;
    """
}

def generate_reports():
    os.makedirs(REPORT_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    
    for filename, query in queries.items():
        try:
            df = pd.read_sql_query(query, conn)
            output_path = os.path.join(REPORT_DIR, filename)
            df.to_csv(output_path, index=False)
            print(f"Generated: {output_path} (Total unique properties: {len(df)})")
        except Exception as e:
            print(f"Error generating {filename}: {e}")
            
    conn.close()

if __name__ == "__main__":
    generate_reports()