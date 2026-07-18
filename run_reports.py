import sqlite3
import pandas as pd
import os

DB_PATH = 'scraper/output/leads.sqlite3'
REPORT_DIR = 'output/reports'

# Define your queries
queries = {
    "developer_whales.csv": "SELECT l.address, count(pi.id) as project_count FROM leads l JOIN permit_insights pi ON l.id = pi.lead_id WHERE pi.intent_category = 'Expansion' GROUP BY l.id HAVING project_count > 1 ORDER BY project_count DESC;",
    "active_velocity.csv": "SELECT l.address, count(pd.id) as recent_permits FROM leads l JOIN permit_details pd ON l.id = pd.lead_id WHERE pd.date_processed > date('now', '-90 days') GROUP BY l.id HAVING recent_permits > 1 ORDER BY recent_permits DESC;",
    "priority_prospects.csv": "SELECT l.address, l.contact_name, pi.intent_category, pi.description FROM leads l JOIN permit_insights pi ON l.id = pi.lead_id WHERE pi.intent_category IN ('Expansion', 'Renovation');"
}

def generate_reports():
    conn = sqlite3.connect(DB_PATH)
    for filename, query in queries.items():
        df = pd.read_sql_query(query, conn)
        df.to_csv(os.path.join(REPORT_DIR, filename), index=False)
        print(f"Generated: {REPORT_DIR}/{filename}")
    conn.close()

if __name__ == "__main__":
    generate_reports()
