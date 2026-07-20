import os
import re
import json
import sys
import asyncio
import random
print("LOADED scrape_redfin.py")
from playwright.async_api import async_playwright

from sqlalchemy import create_engine, text
from db_utils import upsert_lead
from dotenv import load_dotenv


# --------------------------------------------------
# ENV
# --------------------------------------------------

load_dotenv()


DATABASE_URL = os.getenv("DATABASE_URL")


if not DATABASE_URL:

    print("DATABASE_URL missing")
    sys.exit(1)


DATABASE_URL = DATABASE_URL.replace(
    "postgres://",
    "postgresql://",
    1
)


engine = create_engine(
    DATABASE_URL
)



# --------------------------------------------------
# PARSER
# --------------------------------------------------

try:

    from scraper.parse_redfin_html import parse_listing

except Exception as e:

    print(
        "Parser unavailable:",
        e
    )

    parse_listing = None



# --------------------------------------------------
# TASKS
# --------------------------------------------------

def get_tasks():

    with engine.begin() as conn:

        return conn.execute(
            text(
                """
                SELECT
                    id,
                    payload
                FROM ai_tasks
                WHERE
                    task_type='scrape_listing'
                    AND status='pending'
                ORDER BY id
                LIMIT 20
                """
            )
        ).fetchall()



def update_task(
    task_id,
    status
):

    with engine.begin() as conn:

        conn.execute(
            text(
                """
                UPDATE ai_tasks
                SET status=:status
                WHERE id=:id
                """
            ),
            {
                "id": task_id,
                "status": status
            }
        )



# --------------------------------------------------
# ADDRESS FALLBACK
# --------------------------------------------------

def address_from_url(url):

    match = re.search(
        r'/([^/]+)-\d{5}/home',
        url
    )


    if not match:

        return None


    return (
        match.group(1)
        .replace(
            "-",
            " "
        )
        .title()
    )



# --------------------------------------------------
# SAVE
# --------------------------------------------------

def save_lead(
    data,
    url,
    note
):
    address = data.get("address")
    if not address:
        return
    
    normalized_address = address.strip().lower()
    city = data.get("city", "San Francisco")
    parcel_number = data.get("parcel_number")
    
    price_val = data.get("price")
    assessed_value = None
    if price_val:
        if isinstance(price_val, (int, float)):
            assessed_value = float(price_val)
        else:
            cleaned = re.sub(r'[^0-9.]', '', str(price_val))
            if cleaned:
                assessed_value = float(cleaned)

    try:
        upsert_lead(
            normalized_address=normalized_address,
            city=city,
            address=address,
            parcel_number=parcel_number,
            assessed_value=assessed_value,
            status="new"
        )
        print(f"Upserted lead into production: {address}")
    except Exception as e:
        print(f"Upsert error for {address}: {e}")


# --------------------------------------------------
# REDFIN PLAYWRIGHT FETCH
# --------------------------------------------------

async def fetch_redfin(
    page,
    url
):

    print(
        "OPENING PAGE"
    )


    try:

        await page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=60000
        )


        await page.wait_for_timeout(
            5000
        )


    except Exception as e:

        print(
            "PAGE ERROR:",
            e
        )

        return None



    title = await page.title()


    print(
        "TITLE:",
        title
    )



    html = await page.content()


    print(
        "HTML SIZE:",
        len(html)
    )



    # save debugging copy

    try:

        with open(
            "scraper/redfin_live_debug.html",
            "w",
            encoding="utf-8"
        ) as f:

            f.write(html)


        print(
            "Saved scraper/redfin_live_debug.html"
        )


    except Exception as e:

        print(
            "DEBUG SAVE ERROR:",
            e
        )



    if len(html) < 50000:

        print(
            "HTML TOO SMALL"
        )

        return None



    if "Access Denied" in html:

        print(
            "ACCESS DENIED"
        )

        return None



    return html



# --------------------------------------------------
# PROCESS
# --------------------------------------------------

async def process(
    task,
    page
):

    task_id = task.id


    payload = task.payload


    if isinstance(
        payload,
        str
    ):

        payload=json.loads(
            payload
        )


    url = payload.get(
        "url"
    )


    print()
    print(
        "TASK:",
        task_id
    )

    print(
        url
    )



    fallback = {

        "address":
            address_from_url(url),

        "price":
            None,

        "beds":
            None,

        "baths":
            None,

        "sqft":
            None

    }



    html = await fetch_redfin(
        page,
        url
    )



    if not html:

        print(
            "BLOCKED - leaving pending"
        )

        return



    data = fallback



    if parse_listing:

        try:

            parsed = parse_listing(
                html,
                url
            )


            if parsed:

                data.update(
                    parsed
                )


        except Exception as e:

            print(
                "PARSER ERROR:",
                e
            )



    print(
        "DATA:",
        data
    )



    save_lead(
        data,
        url,
        "v8.0 Playwright Redfin scraper"
    )


    update_task(
        task_id,
        "completed"
    )



# --------------------------------------------------
# MAIN
# --------------------------------------------------

async def main():

    print(
        "Starting Redfin Worker v8.0"
    )


    tasks=get_tasks()


    print(
        "Pending:",
        len(tasks)
    )


    if not tasks:

        print(
            "Complete"
        )

        return



    async with async_playwright() as p:


        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox"
            ]
        )


        context = await browser.new_context(

            viewport={
                "width": 1280,
                "height": 900
            },

            user_agent=(
                "Mozilla/5.0 "
                "(Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/127.0 Safari/537.36"
            )

        )


        page = await context.new_page()



        for task in tasks:


            await process(
                task,
                page
            )


            await asyncio.sleep(
                random.uniform(
                    3,
                    6
                )
            )



        await browser.close()

# --------------------------------------------------
# ENTRYPOINT
# --------------------------------------------------

if __name__ == "__main__":

    print("CALLING MAIN")

    asyncio.run(
        main()
    )