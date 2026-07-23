import asyncio
import json
import re
from pathlib import Path

from playwright.async_api import async_playwright

from db_pool import get_pooled_connection


ZIP_CODES = [
    "94506",
    "94507",
    "94518",
    "94519",
    "94520",
    "94521",
    "94523",
    "94526",
    "94549",
    "94556",
    "94595",
]


USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 "
    "Chrome/126 Safari/537.36"
)


def extract_redfin_urls(html):

    urls=set()

    patterns=[
        r'https://www\.redfin\.com/CA/[^"\s]+/home/\d+',
        r'\\/CA\\/[^"]+\\/home\\/\\d+',
        r'/CA/[^"\s]+/home/\d+'
    ]


    for pattern in patterns:

        for m in re.findall(pattern,html):

            m=m.replace("\\/","/")

            if m.startswith("/"):
                m="https://www.redfin.com"+m

            urls.add(m)


    return list(urls)



async def discover_redfin(context, zipcode):


    url=f"https://www.redfin.com/zipcode/{zipcode}"

    print("[REDFIN]",url)


    page=await context.new_page()


    responses=[]


    page.on(
        "response",
        lambda r: responses.append(r.url)
        if "api" in r.url.lower()
        else None
    )


    try:

        response=await page.goto(
            url,
            wait_until="networkidle",
            timeout=90000
        )


        print(
            "[STATUS]",
            response.status if response else None
        )


        await page.wait_for_timeout(8000)


        html=await page.content()


        Path(
            f"debug_{zipcode}.html"
        ).write_text(html)


    except Exception as e:

        print(
            "FAILED",
            zipcode,
            e
        )

        await page.close()
        return []


    await page.close()


    urls=extract_redfin_urls(html)


    print(
        "[FOUND]",
        zipcode,
        len(urls)
    )


    if not urls:

        print(
            "No listings. Saved debug file"
        )


    return [
        u for u in urls
        if zipcode in u
    ]



def enqueue_listing(url):


    payload={
        "url":url,
        "source":"redfin",
        "task":"scrape_listing"
    }


    with get_pooled_connection() as conn:

        with conn.cursor() as cur:


            cur.execute(
            """
            SELECT id
            FROM ai_tasks
            WHERE task_type='scrape_listing'
            AND payload->>'url'=%s
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

    total=0


    async with async_playwright() as p:


        browser=await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox"
            ]
        )


        context=await browser.new_context(
            user_agent=USER_AGENT,
            viewport={
                "width":1440,
                "height":1200
            },
            locale="en-US",
            timezone_id="America/Los_Angeles"
        )


        await context.add_init_script(
        """
        Object.defineProperty(
          navigator,
          'webdriver',
          {
           get:()=>undefined
          }
        )
        """
        )


        for zipcode in ZIP_CODES:


            listings=await discover_redfin(
                context,
                zipcode
            )


            for url in listings:

                if enqueue_listing(url):
                    total+=1



        await browser.close()


    print(
        "Discovery complete:",
        total
    )




def main():

    print(
        "Starting Redfin discovery"
    )


    asyncio.run(run())



if __name__=="__main__":
    main()