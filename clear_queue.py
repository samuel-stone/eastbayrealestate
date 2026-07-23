import os
import psycopg2

DATABASE_URL = os.getenv("DATABASE_URL")

def clear_queues():
    if not DATABASE_URL:
        print("[!] DATABASE_URL environment variable is not set.")
        return
        
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        print("[*] Clearing redfin_scrape_queue...")
        cur.execute("""
            UPDATE redfin_scrape_queue
            SET status = 'completed', completed_at = NOW()
            WHERE status IS NULL OR status IN ('queued', 'running');
        """)
        
        conn.commit()
        print("[+] Queue successfully cleared and marked as completed.")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"[!] Error clearing queue (DB might be in read-only mode if disk is full): {e}")

if __name__ == "__main__":
    clear_queues()
