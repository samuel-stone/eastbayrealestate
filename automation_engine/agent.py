import time
from datetime import datetime

from automation_engine.agent_memory import (
    init_memory,
    remember
)

from automation_engine.agent_brain import analyze_system

from automation_engine.agent_actions import (
    retry_failed_jobs
)


def think():

    print("\nAGENT THINKING:", datetime.now())

    report = analyze_system()


    print("\nOBSERVATIONS:")

    for item in report["observations"]:
        print("-", item)


    print("\nDECISIONS:")

    for decision in report["decisions"]:
        print("-", decision)


    if "Retry failed jobs" in report["decisions"]:

        retry_failed_jobs()


    remember(
        str(report)
    )


def main():

    print("East Bay Automation Agent online")

    init_memory()

    while True:

        think()

        time.sleep(300)


if __name__ == "__main__":
    main()
