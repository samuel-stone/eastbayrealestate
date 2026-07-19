import time
import signal

from datetime import datetime

from automation_engine.environment import validate_environment
from automation_engine.agent_brain import analyze_system


running = True


def shutdown(signum, frame):

    global running

    print(
        "Agent shutting down..."
    )

    running = False



signal.signal(signal.SIGTERM, shutdown)
signal.signal(signal.SIGINT, shutdown)



def main():

    validate_environment()

    print(
        "East Bay Autonomous Agent Online"
    )


    while running:

        try:

            report = analyze_system()

            print(
                "Agent report generated. Check docs/ and planning/ directories."
            )


        except Exception as e:

            print(
                "Agent failure:",
                e
            )


        time.sleep(
            900
        )


    print(
        "Agent stopped cleanly"
    )



if __name__ == "__main__":

    main()