import time
import signal
import traceback

from datetime import datetime

from automation_engine.database import (
    get_job,
    complete_job,
    fail_job,
    log_event
)

from automation_engine.task_registry import run_task


running = True



def shutdown(signum, frame):
    """
    Graceful worker shutdown.
    """

    global running

    print(
        "[WORKER] Shutdown signal received."
    )

    running = False



signal.signal(
    signal.SIGTERM,
    shutdown
)

signal.signal(
    signal.SIGINT,
    shutdown
)



def safe_log_event(
    job_id,
    event_type,
    message,
    metadata=None
):
    """
    Logging should never crash the worker.
    """

    try:

        log_event(
            job_id,
            event_type,
            message,
            metadata or {}
        )

    except Exception as e:

        print(
            "[WORKER] Logging failure:",
            e
        )



def process_job(job):

    job_id = job["id"]
    job_name = job["name"]

    started_at = datetime.now()


    print(
        f"[WORKER] Starting job {job_id}: {job_name}"
    )


    safe_log_event(
        job_id,
        "started",
        f"Started job {job_name}",
        {
            "attempt": job.get(
                "attempts",
                0
            ) + 1,
            "started_at": started_at.isoformat()
        }
    )


    try:

        result = run_task(job)


        finished_at = datetime.now()

        duration = (
            finished_at - started_at
        ).total_seconds()


        safe_log_event(
            job_id,
            "completed",
            f"Completed job {job_name}",
            {
                "result": result,
                "duration_seconds": duration,
                "completed_at": finished_at.isoformat()
            }
        )


        complete_job(job_id)


        print(
            f"[WORKER] Completed job {job_id} "
            f"in {duration:.2f}s"
        )


    except Exception as e:

        error_trace = traceback.format_exc()


        print(
            f"[WORKER] Failed job {job_id}: {e}"
        )


        safe_log_event(
            job_id,
            "failed",
            f"Job failed: {str(e)}",
            {
                "exception_type": type(e).__name__,
                "traceback": error_trace[-3000:]
            }
        )


        fail_job(
            job_id,
            e
        )



def main():

    print(
        "Automation Worker online"
    )


    while running:

        try:

            job = get_job()


            if not job:

                print(
                    "[WORKER] No jobs"
                )

                time.sleep(10)

                continue


            process_job(job)


        except Exception as e:

            print(
                "[WORKER] Loop failure:",
                e
            )

            traceback.print_exc()

            time.sleep(10)


    print(
        "[WORKER] Shutdown complete."
    )



if __name__ == "__main__":
    main()