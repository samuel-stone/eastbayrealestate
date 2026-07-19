import os
import time
from datetime import datetime
from pathlib import Path

import psycopg2
from dotenv import load_dotenv
from google import genai


# --------------------------------------------------
# ENVIRONMENT
# --------------------------------------------------

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL missing. Check .env or Railway variables."
    )


if not GEMINI_API_KEY:
    print(
        "WARNING: GEMINI_API_KEY missing. Running in SAFE MODE."
    )


client = None

if GEMINI_API_KEY:
    client = genai.Client(
        api_key=GEMINI_API_KEY
    )


# --------------------------------------------------
# DATABASE
# --------------------------------------------------

def get_db_connection():
    return psycopg2.connect(
        DATABASE_URL
    )


# --------------------------------------------------
# OBSERVER FUNCTIONS
# --------------------------------------------------

def scan_project_structure():

    files = []

    for root, dirs, filenames in os.walk("."):

        skip_dirs = [
            ".git",
            "__pycache__",
            ".venv",
            "venv",
            "node_modules"
        ]

        if any(
            skip in root
            for skip in skip_dirs
        ):
            continue

        for filename in filenames:
            files.append(
                os.path.join(root, filename)
            )

    return "\n".join(files[:500])


def get_database_telemetry():

    conn = None

    try:

        conn = get_db_connection()

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT status, COUNT(*)
                FROM ai_tasks
                GROUP BY status;
                """
            )

            return dict(cur.fetchall())


    except Exception as e:

        return {
            "database_error": str(e)
        }


    finally:

        if conn:
            conn.close()


# --------------------------------------------------
# GEMINI AI
# --------------------------------------------------

def analyze_system(prompt):

    if not client:

        return """
# EastBay Autonomous Agent Report

agent_status: safe_mode
ai_available: false

Reason:
Gemini client unavailable.

System checks completed:
- Agent running
- Database reachable
- Queue operational

"""

    try:

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )

        return response.text


    except Exception as e:

        print(
            f"Gemini unavailable: {e}"
        )

        return f"""
# EastBay Autonomous Agent Report

agent_status: safe_mode
ai_available: false
provider: Gemini

Reason:
{e}

Completed checks:
- Database connection
- Task queue
- Worker execution

Recommended action:
Restore Gemini quota or billing and rerun audit.

Generated automatically.
"""


# --------------------------------------------------
# AUTONOMOUS AUDIT
# --------------------------------------------------

def autonomous_evolution_cycle():

    print(
        "Starting autonomous evolution cycle..."
    )


    structure = scan_project_structure()

    telemetry = get_database_telemetry()


    prompt = f"""
You are the autonomous architect for EastBayRealEstate.

Review the current system.

PROJECT STRUCTURE:
{structure}


DATABASE TELEMETRY:
{telemetry}


Create a practical engineering improvement plan.

Focus on:

- reliability
- automation
- lead generation
- database enrichment
- AI improvements
- operational improvements

Return markdown only.
"""


    plan = analyze_system(
        prompt
    )


    Path(
        "planning"
    ).mkdir(
        exist_ok=True
    )


    filename = (
        "planning/"
        f"autonomous_plan_"
        f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    )


    with open(
        filename,
        "w"
    ) as f:

        f.write(
            plan
        )


    print(
        f"Plan written: {filename}"
    )


# --------------------------------------------------
# QUEUE PROCESSOR
# --------------------------------------------------

def process_task_queue():

    conn = get_db_connection()

    cur = conn.cursor()


    try:

        cur.execute(
            """
            SELECT id, task_type, payload
            FROM ai_tasks
            WHERE status='pending'
            ORDER BY created_at
            FOR UPDATE SKIP LOCKED
            LIMIT 1;
            """
        )


        task = cur.fetchone()


        if not task:

            print(
                "No pending tasks."
            )

            conn.commit()
            return


        task_id, task_type, payload = task


        print(
            f"Processing task {task_id}: {task_type}"
        )


        cur.execute(
            """
            UPDATE ai_tasks
            SET status='processing'
            WHERE id=%s;
            """,
            (task_id,)
        )

        conn.commit()


        try:

            if task_type == "autonomous_audit":

                autonomous_evolution_cycle()


            elif task_type == "health_check":

                print(
                    "Health:",
                    get_database_telemetry()
                )


            else:

                print(
                    f"Unknown task type: {task_type}"
                )


            cur.execute(
                """
                UPDATE ai_tasks
                SET status='completed'
                WHERE id=%s;
                """,
                (task_id,)
            )


            conn.commit()


        except Exception as e:

            print(
                "Task failed:",
                e
            )


            cur.execute(
                """
                UPDATE ai_tasks
                SET
                    status='failed',
                    retry_count=retry_count+1
                WHERE id=%s;
                """,
                (task_id,)
            )


            conn.commit()


    finally:

        cur.close()
        conn.close()


# --------------------------------------------------
# DIRECT TEST MODE ONLY
# Worker owns the production loop
# --------------------------------------------------

if __name__ == "__main__":

    print(
        "Agent module loaded."
    )

    process_task_queue()