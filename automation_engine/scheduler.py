import time
from datetime import datetime

from automation_engine.database import add_job, get_connection
from automation_engine.schedules import SCHEDULES


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


def main():

    print("Scheduler started")

    while True:

        print("checking schedules...", datetime.now())

        for schedule in SCHEDULES:

            name = schedule["name"]

            if not job_exists(name):
                add_job(name)
                print("queued:", name)

        time.sleep(60)


if __name__ == "__main__":
    main()
