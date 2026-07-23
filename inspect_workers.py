import os
import psycopg2

DATABASE_URL = os.getenv("DATABASE_URL")

def inspect_worker_state():
    if not DATABASE_URL:
        print("[!] DATABASE_URL is not set.")
        return
        
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        print("\n=== AI Tasks / Worker Queue Status ===")
        cur.execute("SELECT task_name, status, COUNT(*) FROM ai_tasks GROUP BY task_name, status;")
        tasks = cur.fetchall()
        if tasks:
            for task_name, status, count in tasks:
                print(f"Task: {task_name} | Status: {status} | Count: {count}")
        else:
            print("No rows found in ai_tasks table.")
            
        print("\n=== Redfin Scrape Queue Status ===")
        cur.execute("SELECT status, COUNT(*) FROM redfin_scrape_queue GROUP BY status;")
        redfin_counts = cur.fetchall()
        if redfin_counts:
            for status, count in redfin_counts:
                print(f"Status: {status} | Count: {count}")
        else:
            print("No rows found in redfin_scrape_queue table.")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"[!] Error inspecting worker state: {e}")

if __name__ == "__main__":
    inspect_worker_state()
