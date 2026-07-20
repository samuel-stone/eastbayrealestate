from automation_engine.environment import validate_environment

import time
import signal

from datetime import datetime

from automation_engine.database import (
    init_db,
    get_job,
    complete_job,
    fail_job
)

from automation_engine.task_registry import run_task


running = True


def shutdown(signum, frame):
    global running

    print(
        "\nWorker shutdown signal received"
    )

    running = False


signal.signal(signal.SIGTERM, shutdown)
signal.signal(signal.SIGINT, shutdown)


def main():

    validate_environment()

    init_db()

    print(
        "East Bay Automation Worker online"
    )


    while running:

        try:

            print(
                "Worker heartbeat:",
                datetime.now()
            )


            job = get_job()


            if job:

                print(
                    "found job:",
                    job
                )


                try:

                    run_task(job)

                    complete_job(
                        job["id"]
                    )

                    print(
                        "completed:",
                        job["name"]
                    )


                except Exception as e:

                    print(
                        "TASK FAILED:",
                        e
                    )

                    fail_job(
                        job["id"],
                        e
                    )


            else:

                print(
                    "no jobs"
                )


        except Exception as e:

            print(
                "WORKER ERROR:",
                e
            )


        time.sleep(10)


    print(
        "Worker stopped cleanly"
    )


if __name__ == "__main__":
    main()