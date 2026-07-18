import sqlite3
import pandas as pd

# Connect to the database
conn = sqlite3.connect('scraper/output/leads.sqlite3')

# Updated query to include city and ensure address details are captured
query = """
    SELECT l.id, l.address, l.city, f.building_permit_count_24m, f.major_project_type 
    FROM leads l
    JOIN prospect_features f ON l.id = f.lead_id
    WHERE f.building_permit_count_24m >= 2 
    ORDER BY f.building_permit_count_24m DESC
"""

df = pd.read_sql_query(query, conn)
df.to_csv('high_priority_leads.csv', index=False)
print("Export complete: high_priority_leads.csv (now with city included)")
conn.close()
