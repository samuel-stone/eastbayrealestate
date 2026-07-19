from datetime import datetime, timedelta

from automation_engine.agent_tools import (
    failed_jobs,
    recent_jobs,
    schedule_engine_task,
    document_run_summary,
    draft_enrichment_plan,
    generate_scraper_script  # <--- New Import
)
from automation_engine.agent_actions import retry_failed_jobs


def analyze_system():

    observations = []
    decisions = []

    failures = failed_jobs()

    if failures:
        observations.append(
            f"{len(failures)} failed jobs detected"
        )

        retry_failed_jobs()
        decisions.append("Retry failed jobs")
        
        document_run_summary(
            "Error Recovery",
            f"Detected and re-queued {len(failures)} failed jobs."
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

    # 1. Trigger routine market report
    schedule_engine_task("daily_market_report")
    decisions.append("Scheduled 'daily_market_report'")
    
    # 2. Draft the strategy
    plan_status = draft_enrichment_plan(
        target_source="Zillow_Redfin", 
        context_notes="Need to bypass Cloudflare/DataDome gates to acquire deeper property history and valuation estimates."
    )
    decisions.append("Drafted scraper integration plan")
    
    # 3. Write the actual Python code
    code_status = generate_scraper_script(target_source="Zillow_Redfin")
    decisions.append("Wrote executable Playwright scraper script")
    
    # 4. Document everything
    document_run_summary(
        "Autonomous Engineering", 
        f"Observations: {observations}.\n{plan_status}\n{code_status}"
    )

    return {
        "time": datetime.now(),
        "observations": observations,
        "decisions": decisions
    }