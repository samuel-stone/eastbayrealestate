import time
from datetime import datetime

from automation_engine.agent_actions import retry_failed_jobs
from automation_engine.agent_tools import (
    failed_jobs,
    recent_jobs
)

from automation_engine.agent_memory import (
    init_memory,
    remember
)


def think():

    print("\nAGENT THINKING:", datetime.now())

    failures = failed_jobs()

    if failures:

        print("Failures detected:", len(failures))

        retry_failed_jobs()

        note = f"Detected and attempted recovery on failures: {failures}"

        print(note)

        remember(note)

    else:

        note = "System healthy"

        print(note)

        remember(note)


    print("\nRecent jobs:")

    for job in recent_jobs():
        print(job)



def main():

    print("East Bay Automation Agent online")

    init_memory()

    while True:

        think()

        time.sleep(300)



if __name__ == "__main__":
    main()