import os
import json
import time
import signal
import sys
from datetime import datetime, timezone
import psycopg2
from dotenv import load_dotenv

# --------------------------------------------------
# ENVIRONMENT
# --------------------------------------------------
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

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
        cur.execute("""
            SELECT COUNT(*)
            FROM ai_tasks
            WHERE task_type='autonomous_audit'
            AND status IN ('pending','processing');
        """)
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        return count > 0
    except Exception as e:
        print(f"Database error in audit_already_pending: {e}")
        return True # Default to True to avoid spamming if DB is glitchy

def enqueue_job():
    if audit_already_pending():
        print("Scheduler: Audit already queued. Skipping.")
        return

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        payload = {
            "action": "daily_health_check",
            "source": "scheduler",
            "requested_at": datetime.now(timezone.utc).isoformat()
        }
        cur.execute("""
            INSERT INTO ai_tasks (task_type, payload, status)
            VALUES ('autonomous_audit', %s, 'pending');
        """, (json.dumps(payload),))
        conn.commit()
        cur.close()
        conn.close()
        print("Scheduler: Autonomous audit queued.")
    except Exception as e:
        print(f"Scheduler Error during enqueue: {e}")

# --------------------------------------------------
# MAIN LOOP
# --------------------------------------------------
if __name__ == "__main__":
    print("Scheduler started. Monitoring schedule...")
    while running:
        enqueue_job()
        
        # Sleep in intervals so we can react to shutdown signals
        for _ in range(60): # 60 * 60 seconds = 1 hour cycle
            if not running:
                break
            time.sleep(60)

    print("Scheduler stopped cleanly.")
    sys.exit(0)