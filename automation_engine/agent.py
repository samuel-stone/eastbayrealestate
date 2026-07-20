from automation_engine.environment import validate_environment

import time
from datetime import datetime

from automation_engine.analysis_engine import analyze_system
from automation_engine.agent_actions import (
    queue_job,
    retry_failed_jobs
)


running = True



def main():

    validate_environment()

    print(
        "East Bay Agent online"
    )


    while running:

        try:

            print(
                "Agent heartbeat:",
                datetime.now()
            )


            #
            # Ask analysis engine what needs attention
            #
            analysis = analyze_system()


            print(
                "Agent analysis:",
                analysis
            )


            #
            # Recover failed jobs
            #
            retry_failed_jobs()


            #
            # Queue jobs based on analysis
            #
            if isinstance(analysis, dict):

                jobs = analysis.get(
                    "jobs",
                    []
                )

                for job in jobs:

                    queue_job(
                        job
                    )


        except Exception as e:

            print(
                "AGENT ERROR:",
                e
            )


        time.sleep(60)



if __name__ == "__main__":

    main()