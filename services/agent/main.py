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
        "DATABASE_URL missing."
    )


client = None

if GEMINI_API_KEY:
    client = genai.Client(
        api_key=GEMINI_API_KEY
    )
else:
    print(
        "WARNING: Gemini key missing. Safe mode enabled."
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

        ignored = [
            ".git",
            "__pycache__",
            ".venv",
            "venv",
            "node_modules"
        ]

        if any(
            item in root
            for item in ignored
        ):
            continue


        for filename in filenames:

            files.append(
                os.path.join(
                    root,
                    filename
                )
            )


    return "\n".join(files)



def get_database_telemetry():

    try:

        conn = get_db_connection()
        cur = conn.cursor()


        cur.execute(
            """
            SELECT status, COUNT(*)
            FROM ai_tasks
            GROUP BY status;
            """
        )


        result = cur.fetchall()


        cur.close()
        conn.close()


        return result


    except Exception as e:

        return {
            "database_error": str(e)
        }



# --------------------------------------------------
# AI ENGINE
# --------------------------------------------------

def analyze_system(prompt):

    if not client:

        return """
# SAFE MODE

Gemini unavailable.

No API key configured.
"""


    try:

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )


        return response.text



    except Exception as e:

        print(
            "Gemini error:",
            e
        )


        if (
            "429" in str(e)
            or
            "RESOURCE_EXHAUSTED" in str(e)
        ):

            raise RuntimeError(
                "TEMP_AI_QUOTA_ERROR"
            )


        raise



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

You are the autonomous architect
for EastBayRealEstate.


Analyze the current system.


PROJECT:

{structure}


DATABASE:

{telemetry}


Create a practical engineering improvement plan.


Focus on:

- reliability
- automation
- lead generation
- database enrichment
- AI improvements
- scalability


Return markdown only.

"""


    report = analyze_system(
        prompt
    )



    Path(
        "planning"
    ).mkdir(
        exist_ok=True
    )


    filename = (
        "planning/"
        "autonomous_plan_"
        f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    )


    with open(
        filename,
        "w"
    ) as f:

        f.write(report)



    print(
        "Plan created:",
        filename
    )



# --------------------------------------------------
# QUEUE PROCESSOR
# --------------------------------------------------

def process_task_queue():

    conn = get_db_connection()
    cur = conn.cursor()


    cur.execute(
        """
        SELECT id, task_type, payload, retry_count
        FROM ai_tasks
        WHERE status='pending'
        ORDER BY created_at
        LIMIT 1;
        """
    )


    task = cur.fetchone()



    if not task:

        print(
            "No pending tasks."
        )

        cur.close()
        conn.close()

        return



    task_id, task_type, payload, retry_count = task



    print(
        f"Processing task {task_id}: {task_type}"
    )



    try:


        if task_type == "autonomous_audit":

            autonomous_evolution_cycle()



        elif task_type == "health_check":

            print(
                "Health check complete."
            )


        else:

            print(
                "Unknown task:",
                task_type
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



    except RuntimeError as e:


        print(
            "Temporary failure:",
            e
        )


        cur.execute(
            """
            UPDATE ai_tasks
            SET
                status='pending',
                retry_count=retry_count+1
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
                status =
                CASE
                    WHEN retry_count >= 3
                    THEN 'failed'
                    ELSE 'pending'
                END,
                retry_count =
                retry_count + 1
            WHERE id=%s;
            """,
            (task_id,)
        )


        conn.commit()



    finally:

        cur.close()
        conn.close()



# --------------------------------------------------
# ENTRY
# --------------------------------------------------

def main():

    print(
        "Agent module loaded."
    )


    while True:

        process_task_queue()

        time.sleep(
            60
        )



if __name__ == "__main__":

    main()