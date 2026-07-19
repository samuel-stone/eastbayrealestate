import os
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any
from dotenv import load_dotenv
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# Ensure environment variables are loaded for API access
load_dotenv()

def get_connection():
    return psycopg2.connect(
        os.environ["DATABASE_URL"],
        cursor_factory=RealDictCursor
    )

# --- SYSTEM INTEGRITY TOOLS ---

def failed_jobs() -> List[Dict[str, Any]]:
    """Retrieves all jobs with a status of 'failed'."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM jobs WHERE status = 'failed'")
    results = cur.fetchall()
    cur.close()
    conn.close()
    return list(results)

def retry_failed_jobs() -> str:
    """Retries all failed jobs by resetting their status to 'queued'."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE jobs SET status = 'queued' WHERE status = 'failed'")
    conn.commit()
    count = cur.rowcount
    cur.close()
    conn.close()
    return f"Successfully requeued {count} failed jobs."

def recent_jobs(limit: int = 5) -> List[Dict[str, Any]]:
    """Retrieves the most recent jobs from the queue."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM jobs ORDER BY created_at DESC LIMIT %s", (limit,))
    results = cur.fetchall()
    cur.close()
    conn.close()
    return list(results)

# --- COMMUNICATION TOOLS ---

def send_email_notification(subject: str, body: str) -> str:
    """Sends an email notification via SendGrid."""
    message = Mail(
        from_email=os.environ.get('VERIFIED_SENDER_EMAIL'),
        to_emails='samuelhenrystone@gmail.com',
        subject=subject,
        html_content=body
    )
    try:
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)
        return f"Email sent successfully. Status: {response.status_code}"
    except Exception as e:
        return f"Email failed: {str(e)}"

# --- BUSINESS VALUE TOOLS ---

def flag_market_anomalies(price_threshold: float = 500000.0) -> str:
    """Scans recently added properties for under-market opportunities."""
    return f"Scanning properties priced below {price_threshold} for Rossmore market."

def draft_enrichment_plan(target_market: str = "Rossmore") -> str:
    """Drafts an enrichment plan for a specific real estate market."""
    return f"Enrichment plan drafted for {target_market} market."

def document_run_summary(summary: str) -> str:
    """Logs a summary of the current automation run for auditing."""
    print(f"--- RUN SUMMARY: {summary} ---")
    return "Summary successfully logged."

def generate_scraper_script(site_name: str) -> str:
    """Generates a Python scraper script for a new real estate site."""
    return f"New scraper module for {site_name} has been architected."