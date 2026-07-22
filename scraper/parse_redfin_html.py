import asyncio
import random
import os
import psycopg2

from psycopg2.extras import RealDictCursor
from playwright.async_api import async_playwright

from scraper.parse_redfin_html import parse_listing


DATABASE_URL = os.getenv("DATABASE_URL")


def get_db_connection():
    return psycopg2.connect(
        DATABASE_URL,
        cursor_factory=RealDictCursor
    )


def get_tasks():

    conn = get_db_connection()
    cur = conn.cursor()

    try:

        cur.execute("""
            SELECT
                id,
                address,
                url
            FROM redfin_scrape_queue
            WHERE status IS NULL
               OR status = 'queued'
            ORDER BY id
            LIMIT 5;
        """)

        tasks = cur.fetchall()

        if tasks:

            ids = [task["id"] for task in tasks]

            cur.execute("""
                UPDATE redfin_scrape_queue
                SET
                    status = 'running',
                    started_at = NOW()
                WHERE id = ANY(%s);
            """, (ids,))

            conn.commit()

        return tasks


    except Exception as e:

        print(f"[!] Error fetching tasks: {e}")
        return []


    finally:

        cur.close()
        conn.close()



def update_queue_status(task_id, status, error=None):

    conn = get_db_connection()
    cur = conn.cursor()

    try:

        cur.execute("""
            UPDATE redfin_scrape_queue
            SET
                status = %s,
                last_error = %s,
                completed_at =
                    CASE
                        WHEN %s = 'completed'
                        THEN NOW()
                        ELSE completed_at
                    END
            WHERE id = %s;
        """, (
            status,
            error,
            status,
            task_id
        ))

        conn.commit()


    except Exception as e:

        print(
            f"[!] Queue update failed: {e}"
        )


    finally:

        cur.close()
        conn.close()



async def process(task, page):

    task_id = task["id"]
    url = task["url"]

    if "redfin.com" not in url:

        print(
            f"[!] Skipping non-Redfin URL: {url}"
        )

        update_queue_status(
            task_id,
            "failed",
            "Non-Redfin URL"
        )

        return


    print(
        f"\nTASK {task_id}"
    )

    print(
        f"URL: {url}"
    )


    try:

        await page.goto(
            url,
            timeout=60000,
            wait_until="domcontentloaded"
        )


        await asyncio.sleep(
            random.uniform(3,5)
        )


        html_content = await page.content()


        data = parse_listing(
            html_content,
            url,
            task["address"]
        )


        if not data:

            print(
                f"[!] Failed parsing {url}"
            )

            update_queue_status(
                task_id,
                "failed",
                "Parser returned no data"
            )

            return



        conn = get_db_connection()
        cur = conn.cursor()


        try:

            cur.execute("""
                INSERT INTO properties
                (
                    address,
                    url,
                    price,
                    beds,
                    baths,
                    sqft,
                    dom,
                    price_drops,
                    is_fixer,
                    last_scraped_at
                )

                VALUES
                (
                    %s,%s,%s,%s,%s,%s,%s,%s,%s,NOW()
                )

                ON CONFLICT(address)

                DO UPDATE SET

                    url = EXCLUDED.url,
                    price = EXCLUDED.price,
                    beds = EXCLUDED.beds,
                    baths = EXCLUDED.baths,
                    sqft = EXCLUDED.sqft,
                    dom = EXCLUDED.dom,
                    price_drops = EXCLUDED.price_drops,
                    is_fixer = EXCLUDED.is_fixer,
                    last_scraped_at = NOW();

            """, (