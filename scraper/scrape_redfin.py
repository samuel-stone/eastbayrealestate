import re
import asyncio
import json
import os
import sys
import random

from playwright.async_api import async_playwright
from sqlalchemy import create_engine, text


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    ""
).replace(
    "postgres://",
    "postgresql://",
    1
)


if not DATABASE_URL:

    print(
        "CRITICAL: DATABASE_URL missing"
    )

    sys.exit(1)



engine = create_engine(
    DATABASE_URL
)



# --------------------------------------------------
# DATABASE
# --------------------------------------------------

def get_pending_tasks():

    with engine.begin() as conn:

        return conn.execute(
            text(
                """
                SELECT
                    id,
                    payload
                FROM ai_tasks
                WHERE status='pending'
                AND task_type='scrape_listing'
                ORDER BY id
                LIMIT 20;
                """
            )
        ).fetchall()



def update_task_status(
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
                "status": status,
                "id": task_id
            }
        )



# --------------------------------------------------
# SAVE LEAD
# --------------------------------------------------

async def save_to_sandbox(
    lead
):

    query = text(
        """
        INSERT INTO leads_sandbox
        (
            address,
            price,
            beds,
            baths,
            sqft,
            property_type,
            last_source_url,
            last_notes,
            status
        )

        VALUES
        (
            :address,
            :price,
            :beds,
            :baths,
            :sqft,
            :property_type,
            :url,
            :notes,
            'new'
        )

        """
    )


    with engine.begin() as conn:

        conn.execute(
            query,
            {

                "address":
                    lead.get(
                        "address",
                        "Unknown"
                    ),


                "price":
                    lead.get(
                        "price"
                    ),


                "beds":
                    lead.get(
                        "beds"
                    ),


                "baths":
                    lead.get(
                        "baths"
                    ),


                "sqft":
                    lead.get(
                        "sqft"
                    ),


                "property_type":
                    "Residential",


                "url":
                    lead.get(
                        "url"
                    ),


                "notes":
                    "Redfin scraper v3.0.2"

            }
        )



# --------------------------------------------------
# EXTRACTION
# --------------------------------------------------

async def extract_listing(
    page,
    url
):


    await page.goto(
        url,
        wait_until="domcontentloaded",
        timeout=60000
    )


    await asyncio.sleep(
        random.uniform(
            4,
            7
        )
    )


    full_text = await page.evaluate(
        "document.body.innerText"
    )


    print(
        "DEBUG PAGE LENGTH:",
        len(full_text)
    )


    print(
        full_text[:500]
    )



    price_match = re.search(
        r'\$([\d,]+)',
        full_text
    )



    beds_match = re.search(
        r'([\d\.]+)\s*(?:Beds?|BD)',
        full_text,
        re.IGNORECASE
    )



    baths_match = re.search(
        r'([\d\.]+)\s*(?:Baths?|BA)',
        full_text,
        re.IGNORECASE
    )



    sqft_match = re.search(
        r'([\d,]+)\s*(?:Sq\.?\s*Ft|Square Feet)',
        full_text,
        re.IGNORECASE
    )



    address_match = re.search(
        r'\d+\s+[A-Za-z0-9\s]+(?:St|Street|Dr|Drive|Ln|Lane|Ct|Court|Way|Rd|Road|Ave|Avenue)',
        full_text
    )



    data = {

        "address":
            address_match.group(0)
            if address_match
            else "Unknown",


        "price":
            float(
                price_match.group(1)
                .replace(",", "")
            )
            if price_match
            else None,


        "beds":
            float(
                beds_match.group(1)
            )
            if beds_match
            else None,


        "baths":
            float(
                baths_match.group(1)
            )
            if baths_match
            else None,


        "sqft":
            float(
                sqft_match.group(1)
                .replace(",", "")
            )
            if sqft_match
            else None,


        "url":
            url

    }



    print(
        "EXTRACTED:",
        data
    )


    return data



# --------------------------------------------------
# PROCESS TASK
# --------------------------------------------------

async def process_task(
    page,
    task
):

    task_id = task.id


    try:

        payload = json.loads(
            task.payload
        )


        url = payload.get(
            "url"
        )


        print(
            "-> Inspecting:",
            url
        )


        listing = await extract_listing(
            page,
            url
        )


        await save_to_sandbox(
            listing
        )


        update_task_status(
            task_id,
            "completed"
        )



    except Exception as e:

        print(
            "TASK FAILED:",
            task_id,
            e
        )


        update_task_status(
            task_id,
            "failed"
        )



# --------------------------------------------------
# WORKER
# --------------------------------------------------

async def run_worker():


    print(
        "Starting Redfin Worker v3.0.2"
    )


    tasks = get_pending_tasks()


    print(
        "Pending tasks:",
        len(tasks)
    )


    if not tasks:

        print(
            "No pending tasks."
        )

        return



    async with async_playwright() as p:


        browser = await p.chromium.launch(
            headless=True
        )


        context = await browser.new_context(
            user_agent=
            "Mozilla/5.0 Chrome/127"
        )


        page = await context.new_page()



        for task in tasks:


            await process_task(
                page,
                task
            )


            await asyncio.sleep(
                random.uniform(
                    3,
                    6
                )
            )



        await browser.close()



    print(
        "Worker batch complete."
    )



# --------------------------------------------------
# ENTRY
# --------------------------------------------------

if __name__ == "__main__":

    asyncio.run(
        run_worker()
    )