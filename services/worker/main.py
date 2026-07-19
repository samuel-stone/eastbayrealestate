import os
import time
import signal

from dotenv import load_dotenv


# --------------------------------------------------
# ENVIRONMENT
# --------------------------------------------------

load_dotenv()


# --------------------------------------------------
# AGENT IMPORT
# --------------------------------------------------

from services.agent.main import process_task_queue


# --------------------------------------------------
# WORKER STATE
# --------------------------------------------------

RUNNING = True


def shutdown_handler(signum, frame):

    global RUNNING

    print(
        "Worker shutdown requested."
    )

    RUNNING = False


signal.signal(
    signal.SIGTERM,
    shutdown_handler
)

signal.signal(
    signal.SIGINT,
    shutdown_handler
)


# --------------------------------------------------
# WORKER LOOP
# --------------------------------------------------

def run():

    print(
        "Worker started. Monitoring ai_tasks..."
    )


    while RUNNING:

        try:

            process_task_queue()


        except Exception as e:

            print(
                "Worker error:",
                e
            )


        time.sleep(60)


    print(
        "Worker stopped cleanly."
    )


# --------------------------------------------------
# ENTRY POINT
# --------------------------------------------------

if __name__ == "__main__":

    run()