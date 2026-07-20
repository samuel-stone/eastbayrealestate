import subprocess
import sys
import os


TASKS = {

    #
    # Scraping
    #

    "scrape_redfin":
        [
            "-m",
            "scraper.scrape_redfin"
        ],


    "scrape_listings":
        [
            "-m",
            "scraper.discover_listings"
        ],


    "discover_listings":
        [
            "-m",
            "scraper.discover_listings"
        ],



    #
    # Lead / Property enrichment
    #

    "process_leads":
        [
            "-m",
            "automation_engine.tasks.process_leads"
        ],


    "enrich_properties":
        [
            "-m",
            "automation_engine.tasks.enrich_properties"
        ],

    "ai_enrichment":
        [
            "-m",
            "automation_engine.tasks.hybrid_ai_enrichment"
        ],

    #
    # Market intelligence
    #

    "analyze_market":
        [
            "-m",
            "prospect_model.analyze_market"
        ],



    #
    # Reporting
    #

    "generate_report":
        [
            "run_reports.py"
        ],


    "daily_market_report":
        [
            "run_reports.py"
        ]

}



def run_task(job):

    name = job["name"]


    if name not in TASKS:

        raise Exception(
            f"Unknown task: {name}"
        )


    command = [
        sys.executable
    ] + TASKS[name]


    print(
        "RUNNING TASK:",
        name
    )


    print(
        "COMMAND:",
        " ".join(command)
    )


    env = os.environ.copy()

    env["PYTHONPATH"] = os.getcwd()



    result = subprocess.run(

        command,

        capture_output=True,

        text=True,

        env=env

    )


    if result.stdout:

        print(
            result.stdout
        )


    if result.stderr:

        print(
            result.stderr
        )


    if result.returncode != 0:

        raise Exception(
            f"Task failed: {name}"
        )


    print(
        "TASK SUCCESS:",
        name
    )
