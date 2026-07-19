import time
from datetime import datetime

from automation_engine.database import get_connection, init_db


SCHEDULES = [
    {
        "name": "scrape_listings",
        "interval_minutes": 5,
    },
    {
        "name": "daily_market_report",
        "interval_minutes": 60,
    },
]


last_run = {}


def enqueue_job(name):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO jobs(name, status)
        VALUES(%s, 'queued')
        """,
        (name,)
    )

    conn.commit()
    cur.close()
    conn.close()

    print(f"queued: {name}")


def should_run(name, interval):
    now = time.time()

    if name not in last_run:
        last_run[name] = now
        return True

    if now - last_run[name] >= interval * 60:
        last_run[name] = now
        return True

    return False


def main():
    init_db()

    print("Scheduler started")

    while True:
        print("checking schedules...", datetime.now())

        for job in SCHEDULES:
            if should_run(job["name"], job["interval_minutes"]):
                enqueue_job(job["name"])

        time.sleep(60)


if __name__ == "__main__":
    main()
