from datetime import datetime

from automation_engine.agent_tools import (
    failed_jobs,
    recent_jobs
)

from automation_engine.agent_memory import remember


def analyze_system():

    print("\nAGENT SUPERVISOR RUNNING")
    print(datetime.now())


    failures = failed_jobs()
    jobs = recent_jobs()


    report = {
        "timestamp": str(datetime.now()),
        "failures": failures,
        "recent_jobs": jobs,
    }


    if failures:

        insight = (
            f"Detected {len(failures)} failed jobs. "
            "Investigate task reliability."
        )

    else:

        insight = (
            "System healthy. "
            "Look for optimization opportunities."
        )


    print(insight)

    remember(
        str(report)
    )


    return report



if __name__ == "__main__":

    analyze_system()
