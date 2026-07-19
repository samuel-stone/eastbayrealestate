import os
import json
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
# DATABASE
# --------------------------------------------------

def get_db_connection():

    return psycopg2.connect(
        DATABASE_URL
    )



# --------------------------------------------------
# SCHEDULER
# --------------------------------------------------

def audit_already_pending():

    conn = get_db_connection()
    cur = conn.cursor()


    cur.execute(
        """
        SELECT COUNT(*)
        FROM ai_tasks
        WHERE task_type='autonomous_audit'
        AND status IN ('pending','processing');
        """
    )


    count = cur.fetchone()[0]


    cur.close()
    conn.close()


    return count > 0



def enqueue_job():

    if audit_already_pending():

        print(
            "Scheduler: Audit already queued. Skipping."
        )

        return



    conn = get_db_connection()
    cur = conn.cursor()



    payload = {

        "action":
            "daily_health_check",

        "source":
            "scheduler",

        "requested_at":
            datetime.now(
                timezone.utc
            ).isoformat()

    }



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
        );
        """,
        (
            json.dumps(payload),
        )
    )



    conn.commit()

    cur.close()
    conn.close()



    print(
        "Scheduler: Autonomous audit queued."
    )



# --------------------------------------------------
# ENTRY
# --------------------------------------------------

if __name__ == "__main__":

    enqueue_job()