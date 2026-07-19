import time
from datetime import datetime


def run_task(job):

    name = job["name"]

    print(
        datetime.now(),
        "Running:",
        name
    )


    if name == "scrape_listings":

        print("Launching scraper pipeline")

        # future:
        # subprocess.run(["python","scraper/scrape_walnut_creek.py"])

        time.sleep(5)

        print("Listings complete")


    elif name == "process_leads":

        print("Running lead scoring")

        # future:
        # subprocess.run(["python","score_prospects.py"])

        time.sleep(3)

        print("Lead processing complete")


    elif name == "daily_market_report":

        print("Generating report")

        # future:
        # subprocess.run(["python","run_reports.py"])

        time.sleep(2)

        print("Report complete")


    else:

        raise Exception(
            f"Unknown task {name}"
        )
