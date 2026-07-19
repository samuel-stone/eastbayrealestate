import os
import json
import time
import signal
import sys
from datetime import datetime, timezone
import psycopg2
from dotenv import load_dotenv

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
# Define your priority focus areas
PRIORITIES = ["SEO_STRATEGY", "CODE_REFACTOR", "DATA_SCRAPING", "DATABASE_ENRICHMENT"]

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL missing.")

# --------------------------------------------------
# STATE & SIGNALS
# --------------------------------------------------
running = True

def shutdown_handler(signum, frame):
    global running
    print("\nScheduler shutdown requested.")
    running = False

signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)

# --------------------------------------------------
# DATABASE LOGIC
# --------------------------------------------------
def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

def audit_already_pending():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM ai_tasks WHERE task_type='autonomous_audit' AND status IN ('pending','processing');")
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        return count > 0
    except Exception as e:
        print(f"Database error: {e}")
        return True

def enqueue_job(priority_index):
    if audit_already_pending():
        print("Scheduler: Audit already queued. Skipping.")
        return

    focus_area = PRIORITIES[priority_index % len(PRIORITIES)]
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        # Including 'focus' in payload so the agent knows what to do
        payload = {
            "action": "autonomous_audit",
            "focus": focus_area,
            "requested_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Adding priority column injection if you applied the SQL ALTER
        cur.execute("""
            INSERT INTO ai_tasks (task_type, payload, status, priority)
            VALUES ('autonomous_audit', %s, 'pending', 1);
        """, (json.dumps(payload),))
        
        conn.commit()
        cur.close()
        conn.close()
        print(f"Scheduler: Queued focus area: {focus_area}")
    except Exception as e:
        print(f"Scheduler Error during enqueue: {e}")

# --------------------------------------------------
# MAIN LOOP
# --------------------------------------------------
if __name__ == "__main__":
    print("Scheduler started. Monitoring schedule...")
    cycle_counter = 0
    while running:
        enqueue_job(cycle_counter)
        cycle_counter += 1
        
        # Sleep for 2 hours per cycle to protect quota (7200 seconds)
        for _ in range(7200):
            if not running:
                break
            time.sleep(1)

    print("Scheduler stopped cleanly.")
    sys.exit(0)