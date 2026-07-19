import psycopg2
from config.config import Registry

# Get connection
conn = psycopg2.connect(Registry.get_db_url(), sslmode='require')
cursor = conn.cursor()

try:
    # Add the column
    cursor.execute("ALTER TABLE prospect_features ADD COLUMN IF NOT EXISTS project_count INTEGER DEFAULT 0;")
    conn.commit()
    print("✓ Success: Column 'project_count' added to 'prospect_features'.")
except Exception as e:
    print(f"Error: {e}")
    conn.rollback()
finally:
    cursor.close()
    conn.close()