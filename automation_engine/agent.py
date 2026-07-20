import os
import psycopg2
import time
from datetime import datetime

from automation_engine.environment import validate_environment
from automation_engine.analysis_engine import analyze_system
from automation_engine.agent_actions import (
    queue_job,
    retry_failed_jobs
)

running = True


def is_job_active(job_name):
    """Check if a job is already queued or running to prevent duplicates."""
    try:
        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM jobs WHERE name = %s AND status IN ('queued', 'running')",
            (job_name,)
        )
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        return count > 0
    except Exception as e:
        print(f"DB Error checking job status for {job_name}: {e}")
        return False


def main():
    validate_environment()
    print("East Bay Agent online")

    while running:
        try:
            print("Agent heartbeat:", datetime.now())

            # Recover failed jobs
            retry_failed_jobs()

            # Ask analysis engine what needs attention
            analysis = analyze_system()
            print("Agent analysis:", analysis)

            # Queue jobs based on analysis
            if isinstance(analysis, dict):
                jobs = analysis.get("jobs", [])
                
                for job in jobs:
                    if not is_job_active(job):
                        queue_job(job)
                    else:
                        print(f"AGENT ACTION: Skipped {job} (already active in queue)")

        except Exception as e:
            print("AGENT ERROR:", e)

        time.sleep(60)


if __name__ == "__main__":
    main()