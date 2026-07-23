import time
import signal
import traceback
from datetime import datetime

from automation_engine.database import (
    get_job,
    complete_job,
    fail_job,
    heartbeat,
    log_event
)

from automation_engine.task_registry import run_task



running = True



def shutdown(sig, frame):

    global running

    print(
        "[WORKER] Shutdown requested"
    )

    running=False



signal.signal(
    signal.SIGTERM,
    shutdown
)

signal.signal(
    signal.SIGINT,
    shutdown
)



def safe_log(
    job_id,
    event,
    message,
    metadata=None
):

    try:

        log_event(
            job_id,
            event,
            message,
            metadata
        )

    except Exception as e:

        print(
            "[LOGGER ERROR]",
            e
        )



def process_job(job):

    job_id = job["id"]

    name = job["name"]


    started=datetime.utcnow()


    print(
        f"[WORKER] Running {job_id}: {name}"
    )


    safe_log(
        job_id,
        "started",
        name
    )


    try:

        heartbeat(job_id)


        result = run_task(job)


        heartbeat(job_id)


        if not result.get(
            "success"
        ):

            raise RuntimeError(
                result.get(
                    "error",
                    "Task failed"
                )
            )


        duration = (
            datetime.utcnow()
            -
            started
        ).total_seconds()


        result["duration_seconds"] = duration


        complete_job(
            job_id,
            result
        )


        safe_log(
            job_id,
            "completed",
            name,
            result
        )


        print(
            f"[WORKER] Complete {job_id} "
            f"{duration:.2f}s"
        )


    except Exception as e:


        traceback_text = traceback.format_exc()


        safe_log(
            job_id,
            "failed",
            str(e),
            {
                "traceback":
                    traceback_text[-3000:]
            }
        )


        fail_job(
            job_id,
            e
        )


        print(
            f"[WORKER] FAILED {job_id}: {e}"
        )



def main():

    print(
        "Automation worker online"
    )


    while running:


        try:


            job=get_job()


            if not job:

                print(
                    "[WORKER] idle"
                )

                time.sleep(10)

                continue


            process_job(job)



        except Exception as e:

            print(
                "[WORKER LOOP ERROR]",
                e
            )

            traceback.print_exc()

            time.sleep(10)



    print(
        "Worker stopped"
    )



if __name__=="__main__":

    main()