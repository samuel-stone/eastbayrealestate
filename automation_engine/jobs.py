from automation_engine.database import get_connection
import json


def add_job(task_type, payload=None):

    conn = get_connection()
    cur = conn.cursor()

    if payload is None:
        payload = {}
        
    # Ensure payload contains the task type so workers/payload inspectors don't fail
    if "task" not in payload:
        payload["task"] = task_type

    cur.execute(
        """
        INSERT INTO ai_tasks
        (
            task_type,
            payload,
            status,
            priority
        )
        VALUES
        (
            %s,
            %s,
            'pending',
            1
        )
        """,
        (
            task_type,
            json.dumps(payload)
        )
    )

    conn.commit()

    cur.close()
    conn.close()

    print("Queued AI task:", task_type)



if __name__ == "__main__":

    add_job(
        "scrape_listing",
        {
            "zip": "94506"
        }
    )