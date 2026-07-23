import json

from automation_engine.database import get_connection



def log_event(
    job_id,
    event_type,
    message,
    metadata=None
):
    """
    Persist structured execution events.

    Examples:
        started
        completed
        failed
        retry
        warning
    """

    if metadata is None:
        metadata = {}


    conn = None

    try:

        conn = get_connection()

        cur = conn.cursor()


        cur.execute(
            """
            INSERT INTO execution_events
            (
                job_id,
                event_type,
                message,
                metadata
            )

            VALUES
            (
                %s,
                %s,
                %s,
                %s::jsonb
            )
            """,
            (
                job_id,
                event_type,
                message,
                json.dumps(metadata)
            )
        )


        conn.commit()

        cur.close()


    except Exception as e:

        print(
            f"[Execution Logger] Failed: {e}"
        )


        if conn:
            conn.rollback()


    finally:

        if conn:
            conn.close()



def get_recent_events(limit=50):

    conn = None

    try:

        conn = get_connection()

        cur = conn.cursor()


        cur.execute(
            """
            SELECT
                e.id,
                e.job_id,
                j.name AS job_name,
                e.event_type,
                e.message,
                e.metadata,
                e.created_at

            FROM execution_events e

            LEFT JOIN jobs j
            ON e.job_id = j.id

            ORDER BY e.created_at DESC

            LIMIT %s
            """,
            (limit,)
        )


        rows = cur.fetchall()


        cur.close()

        return rows


    except Exception as e:

        print(
            f"[Execution Logger] Read failure: {e}"
        )

        return []


    finally:

        if conn:
            conn.close()
