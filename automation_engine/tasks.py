import time


def run_task(job):

    name = job["name"]

    print("Running task:", name)

    if name == "scrape_listings":
        print("Starting scraper...")
        time.sleep(5)
        print("Listings scraped")

    elif name == "process_leads":
        print("Processing leads...")
        time.sleep(3)
        print("Leads processed")

    else:
        print("Unknown task:", name)
