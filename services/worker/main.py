import os
import json
import time
import subprocess
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


def get_db_connection():

    return psycopg2.connect(
        DATABASE_URL,
        cursor_factory=RealDictCursor
    )


def run_python_module(module):

    print(f"Running module: {module}")

    subprocess.run(
        [
            "python",
            "-m",
            module
        ],
        check=True
    )


def execute_task(task_id, task_type, payload):

    print(
        f"Executing {task_type}"
    )


    if task_type in [
        "data_enrichment",
        "hybrid_ai_enrichment"
    ]:

        run_python_module(
            "automation_engine.tasks.hybrid_ai_enrichment"
        )


    elif task_type in [
        "scrape_listing",
        "scrape_listings"
    ]:

        run_python_module(
            "scraper.discover_listings"
        )


    elif task_type == "analyze_market":

        run_python_module(
            "prospect_model.analyze_market"
        )


    elif task_type == "autonomous_audit":

        run_python_module(
            "services.agent.main"
        )


    elif task_type == "research_only":

        run_python_module(
            "services.agent.main"
        )


    else:

        raise Exception(
            f"Unknown task type {task_type}"
        )



def poll_queue():

    print(
        "Worker started. Listening..."
    )


    while True:

        try:

            with get_db_connection() as conn:

                with conn.cursor() as cur:


                    cur.execute(
                    """
                    SELECT id, task_type, payload
                    FROM ai_tasks
                    WHERE status='pending'
                    ORDER BY priority ASC, created_at ASC
                    LIMIT 1
                    FOR UPDATE SKIP LOCKED;
                    """
                    )


                    task = cur.fetchone()


                    if task:

                        task_id = task["id"]

                        task_type = task["task_type"]

                        payload = task["payload"]


                        if isinstance(payload, str):

                            payload = json.loads(payload)



                        print(
                            f"--- Processing Task {task_id}: {task_type} ---"
                        )


                        cur.execute(
                        """
                        UPDATE ai_tasks
                        SET status='in_progress'
                        WHERE id=%s
                        """,
                        (task_id,)
                        )

                        conn.commit()



                        try:

                            execute_task(
                                task_id,
                                task_type,
                                payload
                            )


                            cur.execute(
                            """
                            UPDATE ai_tasks
                            SET status='completed'
                            WHERE id=%s
                            """,
                            (task_id,)
                            )


                            conn.commit()


                            print(
                                f"Completed task {task_id}"
                            )


                        except Exception as e:


                            print(
                                "FAILED:",
                                e
                            )


                            cur.execute(
                            """
                            UPDATE ai_tasks
                            SET status='failed'
                            WHERE id=%s
                            """,
                            (task_id,)
                            )

                            conn.commit()



        except Exception as e:

            print(
                "Worker error:",
                e
            )


        time.sleep(10)



if __name__ == "__main__":

    poll_queue()