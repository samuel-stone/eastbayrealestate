import os
import psycopg2

DATABASE_URL = os.getenv("DATABASE_URL")

def query_redfin():
    if not DATABASE_URL:
        print("[!] DATABASE_URL is not set.")
        return
        
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        print("\n=== Inspecting redfin_scrape_queue Columns ===")
        cur.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'redfin_scrape_queue';
        """)
        columns = cur.fetchall()
        for col in columns:
            print(f" - {col[0]} ({col[1]})")
            
        print("\n=== Sample of Redfin Queue Entries ===")
        # Dynamically select available columns or query safely
        col_names = [c[0] for c in columns]
        select_cols = ", ".join([c for c in ['id', 'url', 'status'] if c in col_names])
        cur.execute(f"SELECT {select_cols} FROM redfin_scrape_queue LIMIT 5;")
        queue_rows = cur.fetchall()
        for row in queue_rows:
            print(row)
            
        print("\n=== Sample of Scraped Properties Data ===")
        cur.execute("SELECT * FROM properties LIMIT 3;")
        prop_rows = cur.fetchall()
        if prop_rows:
            for row in prop_rows:
                print(row)
        else:
            print("No property records found yet.")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"[!] Error querying Redfin data: {e}")

if __name__ == "__main__":
    query_redfin()
