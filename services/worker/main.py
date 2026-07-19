import time
import signal
import sys

from dotenv import load_dotenv


# --------------------------------------------------
# ENVIRONMENT
# --------------------------------------------------

load_dotenv()


from services.agent.main import process_task_queue



# --------------------------------------------------
# WORKER STATE
# --------------------------------------------------

running = True



def shutdown_handler(
    signum,
    frame
):

    global running

    print(
        "\nWorker shutdown requested."
    )

    running = False



signal.signal(
    signal.SIGINT,
    shutdown_handler
)


signal.signal(
    signal.SIGTERM,
    shutdown_handler
)



# --------------------------------------------------
# WORKER LOOP
# --------------------------------------------------

def run():

    print(
        "Worker started. Monitoring ai_tasks..."
    )


    while running:

        try:

            process_task_queue()


        except Exception as e:

            print(
                "Worker error:",
                e
            )


        time.sleep(
            30
        )



    print(
        "Worker stopped cleanly."
    )


    sys.exit(0)



# --------------------------------------------------
# ENTRY
# --------------------------------------------------

if __name__ == "__main__":

    run()