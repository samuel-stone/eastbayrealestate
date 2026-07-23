import asyncio
import os
import random
import json
from pathlib import Path
from datetime import datetime

import psycopg2
from psycopg2.extras import RealDictCursor

from playwright.async_api import async_playwright

from scraper.parse_redfin_html import parse_listing


DATABASE_URL = os.getenv("DATABASE_URL")


DEBUG_DIR = Path("debug/redfin")
PROFILE_DIR = Path("debug/redfin_profile")


DEBUG_DIR.mkdir(
    parents=True,
    exist_ok=True
)

PROFILE_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# --------------------------------------------------
# Database
# --------------------------------------------------

def get_db_connection():

    return psycopg2.connect(
        DATABASE_URL,
        cursor_factory=RealDictCursor
    )


# --------------------------------------------------
# Queue
# --------------------------------------------------

def get_tasks(limit=5):

    conn = get_db_connection()
    cur = conn.cursor()

    try:

        cur.execute(
            """
            SELECT
                id,
                url,
                address
            FROM redfin_scrape_queue
            WHERE status IS NULL
               OR status = 'queued'
            ORDER BY id
            LIMIT %s
            """,
            (
                limit,
            )
        )


        tasks = cur.fetchall()


        if tasks:

            ids = [
                x["id"]
                for x in tasks
            ]


            cur.execute(
                """
                UPDATE redfin_scrape_queue
                SET
                    status='running',
                    started_at=NOW()
                WHERE id = ANY(%s)
                """,
                (
                    ids,
                )
            )


            conn.commit()


        return tasks


    finally:

        cur.close()
        conn.close()



def update_task(
    task_id,
    status,
    error=None
):

    conn = get_db_connection()
    cur = conn.cursor()


    try:

        cur.execute(
            """
            UPDATE redfin_scrape_queue

            SET
                status=%s,
                last_error=%s,

                completed_at =
                    CASE
                        WHEN %s='completed'
                        THEN NOW()
                        ELSE completed_at
                    END

            WHERE id=%s
            """,
            (
                status,
                error,
                status,
                task_id
            )
        )


        conn.commit()


    finally:

        cur.close()
        conn.close()



# --------------------------------------------------
# Validation
# --------------------------------------------------

def validate_data(data):

    if not data:
        return False


    confidence = 0


    if data.get("address"):
        confidence += 25


    if data.get("price"):
        confidence += 25


    if data.get("beds"):
        confidence += 25


    if data.get("sqft"):
        confidence += 25



    address = (
        data.get("address")
        or ""
    ).lower()



    bad_values = [

        "robot",

        "captcha",

        "challenge",

        "are you"

    ]


    for bad in bad_values:

        if bad in address:
            return False



    return confidence >= 50



# --------------------------------------------------
# Debug Capture
# --------------------------------------------------

async def save_debug(
    page,
    task_id
):

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )


    html_file = (
        DEBUG_DIR /
        f"{task_id}_{timestamp}.html"
    )


    png_file = (
        DEBUG_DIR /
        f"{task_id}_{timestamp}.png"
    )


    try:

        html = await page.content()


        html_file.write_text(
            html,
            encoding="utf-8"
        )


        await page.screenshot(
            path=str(png_file),
            full_page=True
        )


        print(
            "[DEBUG]",
            html_file
        )


    except Exception as e:

        print(
            "[DEBUG FAILED]",
            e
        )



# --------------------------------------------------
# Save Property
# --------------------------------------------------

def save_property(data):

    conn = get_db_connection()
    cur = conn.cursor()


    try:

        cur.execute(
            """
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

                url=EXCLUDED.url,
                price=EXCLUDED.price,
                beds=EXCLUDED.beds,
                baths=EXCLUDED.baths,
                sqft=EXCLUDED.sqft,
                dom=EXCLUDED.dom,
                price_drops=EXCLUDED.price_drops,
                is_fixer=EXCLUDED.is_fixer,
                last_scraped_at=NOW()

            """,
            (
                data.get("address"),
                data.get("url"),
                data.get("price"),
                data.get("beds"),
                data.get("baths"),
                data.get("sqft"),
                data.get("dom"),
                data.get("price_drops"),
                data.get("is_fixer")
            )
        )


        conn.commit()


    finally:

        cur.close()
        conn.close()



# --------------------------------------------------
# Scrape One Listing
# --------------------------------------------------

async def process(
    task,
    page
):

    task_id = task["id"]
    url = task["url"]


    print()
    print(
        "Scraping:",
        url
    )


    if "redfin.com" not in url:

        update_task(
            task_id,
            "failed",
            "invalid url"
        )

        return



    try:

        response = await page.goto(
            url,
            timeout=60000,
            wait_until="domcontentloaded"
        )


        await asyncio.sleep(
            random.uniform(
                4,
                7
            )
        )


        html = await page.content()



        if len(html) < 10000:

            await save_debug(
                page,
                task_id
            )

            raise Exception(
                "Suspicious HTML size"
            )



        if (
            "robot" in html.lower()
            or
            "captcha" in html.lower()
        ):

            await save_debug(
                page,
                task_id
            )


            raise Exception(
                "Redfin challenge detected"
            )



        data = parse_listing(
            html,
            url,
            task.get("address")
        )



        print(
            json.dumps(
                data,
                indent=2,
                default=str
            )
        )



        if not validate_data(data):

            await save_debug(
                page,
                task_id
            )


            raise Exception(
                "Low confidence parse"
            )



        save_property(
            data
        )


        update_task(
            task_id,
            "completed"
        )


        print(
            "[DONE]",
            task_id
        )



    except Exception as e:


        print(
            "[FAILED]",
            task_id,
            e
        )


        update_task(
            task_id,
            "failed",
            str(e)
        )



# --------------------------------------------------
# Runner
# --------------------------------------------------

async def run_scraper():

    tasks = get_tasks()


    if not tasks:

        print(
            "No queued tasks"
        )

        return



    async with async_playwright() as p:


        browser = await p.chromium.launch_persistent_context(

            user_data_dir=str(
                PROFILE_DIR
            ),

            headless=True,

            viewport={
                "width":1280,
                "height":900
            },

            locale="en-US"

        )



        page = await browser.new_page()



        await page.add_init_script(
            """
            Object.defineProperty(
                navigator,
                'webdriver',
                {
                    get: () => undefined
                }
            )
            """
        )



        for task in tasks:

            await process(
                task,
                page
            )



        await browser.close()



# --------------------------------------------------
# Automation Entry
# --------------------------------------------------

def main(payload=None):

    print(
        "[Pipeline] scrape_redfin starting"
    )


    asyncio.run(
        run_scraper()
    )



def run(payload=None):

    main(payload)



if __name__ == "__main__":

    main()
