import os
import psycopg2
from scraper.discover_listings import main as discover_main

def run_qa():
    print("==============================")
    print("   EASTBAYREALESTATE QA SUITE ")
    print("==============================")
    
    # 1. Test Database Connectivity & Read/Write
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("[FAIL] DATABASE_URL environment variable is missing.")
        return
        
    try:
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        res = cur.fetchone()
        if res and res[0] == 1:
            print("[PASS] Database connection and query execution successful.")
        else:
            print("[FAIL] Database query returned unexpected result.")
            return
    except Exception as e:
        print(f"[FAIL] Database connection error: {e}")
        return

    # 2. Check Table Schema & Counts
    try:
        cur.execute("SELECT COUNT(*) FROM properties;")
        prop_count = cur.fetchone()[0]
        print(f"[INFO] Properties table count: {prop_count}")
        
        cur.execute("SELECT status, COUNT(*) FROM redfin_scrape_queue GROUP BY status;")
        queues = cur.fetchall()
        print("[INFO] Redfin Queue Status:")
        for status, count in queues:
            print(f"       - {status}: {count}")
    except Exception as e:
        print(f"[FAIL] Failed checking table statistics: {e}")
        return
    finally:
        cur.close()
        conn.close()

    # 3. Test Discovery Execution
    print("\n[*] Running discovery pipeline test...")
    try:
        discover_main()
        print("[PASS] Discovery module executed successfully.")
    except Exception as e:
        print(f"[FAIL] Discovery module crashed: {e}")
        return

    print("\n==============================")
    print("   ALL QA CHECKS COMPLETED    ")
    print("==============================")

if __name__ == "__main__":
    run_qa()
