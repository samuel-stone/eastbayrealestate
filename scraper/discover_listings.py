import asyncio
import json
import re
from pathlib import Path

from playwright.async_api import async_playwright

from db_pool import get_pooled_connection


ZIP_CODES = [
    "94506",
    "94507",
    "94595",
]


USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 "
    "(KHTML, like Gecko) "
    "Chrome/126.0 Safari/537.36"
)



def extract_redfin_urls(html):

    listings = set()


    # Full URLs

    matches = re.findall(
        r"https://www\.redfin\.com/CA/[^\"']+/home/\d+",
        html
    )

    for url in matches:
        listings.add(
            url.replace("\\/", "/")
        )


    # Relative URLs

    matches = re.findall(
        r"/CA/[^\"']+/home/\d+",
        html
    )

    for url in matches:

        listings.add(
            "https://www.redfin.com" + url
        )


    # Listing IDs from JSON

    ids = re.findall(
        r'"propertyId"\s*:\s*"(\d+)"',
        html
    )


    for pid in ids:

        listings.add(
            f"REDFIN_PROPERTY_ID:{pid}"
        )


    return list(listings)



def is_blocked(html):

    signals = [

        "Are You a Robot",

        "Verify you are human",

        "Access Denied",

        "captcha",

        "cloudflare",

        "bot protection"

    ]


    text = html.lower()


    return any(
        x.lower() in text
        for x in signals
    )



async def discover_redfin(context, zipcode):


    url = (
        f"https://www.redfin.com/zipcode/{zipcode}"
    )


    print(
        "[REDFIN] Fetching:",
        url
    )


    page = await context.new_page()


    try:

        response = await page.goto(
            url,
            wait_until="networkidle",
            timeout=60000
        )


        if response:

            print(
                "[REDFIN] Status:",
                response.status
            )


        await page.wait_for_timeout(5000)


        html = await page.content()


    except Exception as e:

        print(
            "[REDFIN] Error",
            e
        )

        await page.close()

        return []


    await page.close()



    if is_blocked(html):

        print(
            "[REDFIN] Block detected",
            zipcode
        )

        Path(
            f"/tmp/redfin_block_{zipcode}.html"
        ).write_text(
            html
        )

        return []



    listings = extract_redfin_urls(html)


    print(
        "[REDFIN]",
        zipcode,
        "found",
        len(listings)
    )


    return listings




def enqueue_listing(url):


    payload = {

        "url": url,

        "source": "redfin",

        "task": "scrape_listing"

    }


    with get_pooled_connection() as conn:

        with conn.cursor() as cur:


            cur.execute(
                """
                SELECT id
                FROM ai_tasks
                WHERE task_type='scrape_listing'
                AND payload->>'url'=%s
                LIMIT 1
                """,
                (url,)
            )


            if cur.fetchone():

                return False



            cur.execute(
                """
                INSERT INTO ai_tasks
                (
                    task_type,
                    payload,
                    status,
                    retry_count
                )

                VALUES
                (
                    'scrape_listing',
                    %s,
                    'pending',
                    0
                )
                """,
                (
                    json.dumps(payload),
                )
            )


        conn.commit()


    print(
        "Queued:",
        url
    )


    return True




async def run():


    total = 0


    async with async_playwright() as p:


        browser = await p.chromium.launch(
            headless=True
        )


        context = await browser.new_context(

            user_agent=USER_AGENT,

            locale="en-US",

            viewport={
                "width":1440,
                "height":1200
            }

        )


        for zipcode in ZIP_CODES:


            listings = await discover_redfin(
                context,
                zipcode
            )


            for listing in listings:

                if enqueue_listing(listing):

                    total += 1



        await browser.close()



    print(
        "Discovery complete:",
        total
    )




def main():

    asyncio.run(run())



if __name__ == "__main__":
    main()