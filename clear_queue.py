import os
import psycopg2

DATABASE_URL = os.getenv("DATABASE_URL")

def clear_completed_queue():
    if not DATABASE_URL:
        print("[!] DATABASE_URL is not set.")
        return
        
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        print("[*] Checking current queue status counts...")
        cur.execute("SELECT status, COUNT(*) FROM redfin_scrape_queue GROUP BY status;")
        for status, count in cur.fetchall():
            print(f"    - {status}: {count}")
            
        print("\n[*] Clearing 'completed' and 'failed' records from redfin_scrape_queue...")
        cur.execute("DELETE FROM redfin_scrape_queue WHERE status IN ('completed', 'failed');")
        deleted_count = cur.rowcount
        conn.commit()
        
        print(f"[+] Successfully removed {deleted_count} old queue entries.")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"[!] Error clearing queue: {e}")

if __name__ == "__main__":
    clear_completed_queue()
