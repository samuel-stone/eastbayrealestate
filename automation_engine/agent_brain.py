from datetime import datetime, timedelta

from automation_engine.agent_tools import (
    failed_jobs,
    recent_jobs
)


def analyze_system():

    observations = []
    decisions = []

    failures = failed_jobs()

    if failures:
        observations.append(
            f"{len(failures)} failed jobs detected"
        )

        decisions.append(
            "Retry failed jobs"
        )

    jobs = recent_jobs()

    if jobs:

        latest = jobs[0]

        observations.append(
            f"Latest job: {latest['name']} ({latest['status']})"
        )

    else:

        observations.append(
            "No recent jobs found"
        )

        decisions.append(
            "Check scheduler"
        )


    return {
        "time": datetime.now(),
        "observations": observations,
        "decisions": decisions
    }
