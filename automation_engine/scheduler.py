import time
from datetime import datetime

from automation_engine.jobs import add_job


def main():
    print("Scheduler started")

    last_run = None

    while True:
        now = datetime.now()

        # run once per day
        if now.hour == 6 and last_run != now.date():
            print("Creating daily scrape job")

            add_job("scrape_listings")

            last_run = now.date()

        else:
            print("scheduler heartbeat:", now)

        time.sleep(60)


if __name__ == "__main__":
    main()
