import os
import psycopg2

DATABASE_URL = os.getenv("DATABASE_URL")

def inspect_leads():
    if not DATABASE_URL:
        print("[!] DATABASE_URL is not set.")
        return
        
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        print("\n=== Checking Tables for Leads/Properties ===")
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public';
        """)
        tables = [t[0] for t in cur.fetchall()]
        print(f"Tables in DB: {tables}")
        
        if 'leads' in tables:
            cur.execute("SELECT COUNT(*) FROM leads;")
            print(f"Total rows in 'leads': {cur.fetchone()[0]}")
            cur.execute("SELECT * FROM leads LIMIT 3;")
            for row in cur.fetchall():
                print(row)
        elif 'properties' in tables:
            cur.execute("SELECT COUNT(*) FROM properties;")
            print(f"Total rows in 'properties': {cur.fetchone()[0]}")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"[!] Error inspecting leads: {e}")

if __name__ == "__main__":
    inspect_leads()
