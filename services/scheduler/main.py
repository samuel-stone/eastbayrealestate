import os
import json
import socket
import uuid

from datetime import datetime, timezone

import psycopg2
from dotenv import load_dotenv


# --------------------------------------------------
# ENVIRONMENT
# --------------------------------------------------

load_dotenv()


DATABASE_URL = os.getenv(
    "DATABASE_URL"
)


if not DATABASE_URL:

    raise RuntimeError(
        "DATABASE_URL missing."
    )


# --------------------------------------------------
# JOB CREATION
# --------------------------------------------------

def enqueue_job():


    payload = {

        "action": "daily_health_check",

        "source": "scheduler",

        "scheduler_host": socket.gethostname(),

        "execution_id": str(
            uuid.uuid4()
        ),

        "requested_at":
            datetime.now(
                timezone.utc
            ).isoformat()

    }


    with psycopg2.connect(
        DATABASE_URL
    ) as conn:


        with conn.cursor() as cur:


            # Prevent duplicate audits

            cur.execute(
                """
                SELECT id
                FROM ai_tasks
                WHERE task_type='autonomous_audit'
                AND status IN
                (
                    'pending',
                    'processing'
                )
                LIMIT 1;
                """
            )


            existing = cur.fetchone()


            if existing:

                print(
                    f"Scheduler: Audit already queued. ID={existing[0]}"
                )

                return



            cur.execute(
                """
                INSERT INTO ai_tasks
                (
                    task_type,
                    payload,
                    status
                )

                VALUES
                (
                    'autonomous_audit',
                    %s,
                    'pending'
                )

                RETURNING id;
                """,

                (
                    json.dumps(payload),
                )
            )


            job_id = cur.fetchone()[0]


            print(
                f"Scheduler: Job {job_id} enqueued."
            )



# --------------------------------------------------
# ENTRY POINT
# --------------------------------------------------

if __name__ == "__main__":

    enqueue_job()