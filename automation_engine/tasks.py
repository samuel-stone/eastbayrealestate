import subprocess
import sys
import os


# --------------------------------------------------
# TASK REGISTRY
# --------------------------------------------------

TASKS = {


    "scrape_redfin":
        [
            "-m",
            "scraper.scrape_redfin"
        ],



    "scrape_listings":
        [
            "-m",
            "scraper.scrape_redfin"
        ],



    "discover_listings":
        [
            "-m",
            "scraper.discover_listings"
        ],



    "scrape_danville":
        [
            "-m",
            "scraper.scrape_danville"
        ],



    "process_leads":
        [
            "-m",
            "prospect_model.score_prospects"
        ],



    "daily_market_report":
        [
            "run_reports.py"
        ],



    "scrape_zillow_redfin":
        [
            "scraper/scrape_zillow_redfin.py"
        ]

}



# --------------------------------------------------
# EXECUTOR
# --------------------------------------------------

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
        "EXECUTING:",
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
        "SUCCESS:",
        name
    )