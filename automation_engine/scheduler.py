import time
from datetime import datetime, timedelta

from automation_engine.database import add_job, get_connection
from automation_engine.schedules import SCHEDULES


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

    if row:
        return row["completed_at"]

    return None


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

    name = schedule["name"]
    interval = schedule["interval"]

    last = last_completed(name)

    if not last:
        return True

    return datetime.now(last.tzinfo) > last + timedelta(seconds=interval)



def main():

    print("Scheduler started")

    while True:

        print("checking schedules...", datetime.now())

        for schedule in SCHEDULES:

            name = schedule["name"]

            if should_run(schedule) and not job_exists(name):

                add_job(name)

                print(
                    "queued:",
                    name
                )

        time.sleep(60)


if __name__ == "__main__":
    main()
