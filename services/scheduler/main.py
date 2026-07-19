import os, json, time, signal, sys
from datetime import datetime, timezone
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

PRIORITIES = [
    "GROWTH_STRATEGY",       # Marketing & Funnel
    "DATA_ENRICHMENT",       # Turning scraped data into lead insights
    "LANDING_PAGE_DEV",      # SEO/SEM funnel development
    "RESEARCH_ONLY",         # Health checks
    "CODE_REFACTOR"          # Tech debt
]

# ... (shutdown handler logic remains the same)

def enqueue_job(priority_index):
    focus_area = PRIORITIES[priority_index % len(PRIORITIES)]
    task_type = "research_only" if focus_area == "RESEARCH_ONLY" else "autonomous_audit"
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    payload = {"focus": focus_area, "requested_at": datetime.now(timezone.utc).isoformat()}
    cur.execute("INSERT INTO ai_tasks (task_type, payload, status, priority) VALUES (%s, %s, 'pending', 1);", 
                (task_type, json.dumps(payload)))
    conn.commit(); cur.close(); conn.close()
    print(f"Scheduler: Queued {task_type} (Focus: {focus_area})")

# ... (main loop with 7200s sleep)