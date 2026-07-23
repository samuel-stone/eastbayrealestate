import os
import psycopg2

DATABASE_URL = os.getenv("DATABASE_URL")

def check_db():
    if not DATABASE_URL:
        print("[!] DATABASE_URL is not set.")
        return
        
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        print("\n--- Properties Table Count ---")
        cur.execute("SELECT COUNT(*) FROM properties;")
        count = cur.fetchone()[0]
        print(f"Total rows in properties: {count}")
        
        print("\n--- Recent Properties ---")
        cur.execute("SELECT id, address, price, last_scraped_at FROM properties ORDER BY id DESC LIMIT 5;")
        rows = cur.fetchall()
        for row in rows:
            print(row)
            
        print("\n--- Redfin Queue Status Breakdown ---")
        cur.execute("SELECT status, COUNT(*) FROM redfin_scrape_queue GROUP BY status;")
        statuses = cur.fetchall()
        for status, q_count in statuses:
            print(f"Status '{status}': {q_count}")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"[!] Error checking database: {e}")

if __name__ == "__main__":
    check_db()
