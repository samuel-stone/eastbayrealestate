import time
import signal
from datetime import datetime, timedelta

from automation_engine.database import add_job, get_connection
from automation_engine.schedules import SCHEDULES


running = True


def shutdown(signum, frame):

    global running

    print("Scheduler shutting down...")

    running = False



signal.signal(signal.SIGTERM, shutdown)
signal.signal(signal.SIGINT, shutdown)



def last_completed(name):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT completed_at
        FROM jobs
        WHERE name=%s
        AND status='completed'
        ORDER BY completed_at DESC
        LIMIT 1
        """,
        (name,)
    )

    row = cur.fetchone()

    conn.close()

    return row["completed_at"] if row else None



def job_exists(name):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT 1
        FROM jobs
        WHERE name=%s
        AND status IN ('queued','running')
        LIMIT 1
        """,
        (name,)
    )

    exists = cur.fetchone()

    conn.close()

    return exists



def should_run(schedule):

    last = last_completed(schedule["name"])

    if not last:
        return True

    return (
        datetime.now(last.tzinfo)
        >
        last + timedelta(seconds=schedule["interval"])
    )



def main():
    from automation_engine.environment import validate_environment
    print("East Bay Scheduler online")

    while running:

        print(
            "Scheduler heartbeat:",
            datetime.now()
        )

        for schedule in SCHEDULES:

            name = schedule["name"]

            if should_run(schedule) and not job_exists(name):

                add_job(name)

                print(
                    "queued:",
                    name
                )


        time.sleep(60)


    print("Scheduler stopped cleanly")



if __name__ == "__main__":
    main()
