import time
from datetime import datetime

from automation_engine.database import (
    init_db,
    get_job,
    complete_job,
    fail_job
)

from automation_engine.tasks import run_task


def main():

    init_db()

    print("Automation worker started")

    while True:

        print("checking queue...", datetime.now())

        job = get_job()

        if job:

            print("found job:", job)

            try:
                run_task(job)
                complete_job(job["id"])
                print("completed")

            except Exception as e:
                print("FAILED:", e)
                fail_job(job["id"], e)

        else:
            print("no jobs")

        time.sleep(10)


if __name__ == "__main__":
    main()
