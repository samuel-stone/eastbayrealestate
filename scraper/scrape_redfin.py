import asyncio
import random
import os
import psycopg2

from psycopg2.extras import RealDictCursor

from playwright.async_api import async_playwright

from scraper.parse_redfin_html import parse_listing



DATABASE_URL = os.getenv(
    "DATABASE_URL"
)



def get_db_connection():

    return psycopg2.connect(
        DATABASE_URL,
        cursor_factory=RealDictCursor
    )




def get_tasks():

    conn = get_db_connection()

    cur = conn.cursor()


    try:

        cur.execute(
            """
            SELECT
                id,
                payload->>'url' AS url
            FROM ai_tasks
            WHERE task_type='scrape_listing'
            AND status='pending'
            ORDER BY priority DESC, created_at
            LIMIT 5
            """
        )


        tasks = cur.fetchall()



        if tasks:

            ids = [
                x["id"]
                for x in tasks
            ]


            cur.execute(
                """
                UPDATE ai_tasks
                SET status='running'
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





def complete_task(task_id):

    conn = get_db_connection()

    cur = conn.cursor()


    cur.execute(
        """
        UPDATE ai_tasks
        SET status='completed'
        WHERE id=%s
        """,
        (
            task_id,
        )
    )


    conn.commit()

    cur.close()

    conn.close()





async def process(task,page):


    task_id = task["id"]

    url = task["url"]


    print(
        "Scraping:",
        url
    )



    try:


        await page.goto(
            url,
            timeout=60000,
            wait_until="domcontentloaded"
        )



        await asyncio.sleep(
            random.uniform(2,5)
        )



        html = await page.content()



        data = parse_listing(
            html,
            url
        )



        if not data:

            raise Exception(
                "Parser returned empty"
            )



        conn = get_db_connection()

        cur = conn.cursor()



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

                price=EXCLUDED.price,
                beds=EXCLUDED.beds,
                baths=EXCLUDED.baths,
                sqft=EXCLUDED.sqft,
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


        complete_task(task_id)



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




async def run_scraper():


    tasks = get_tasks()



    if not tasks:

        print(
            "No Redfin tasks"
        )

        return




    async with async_playwright() as p:


        browser = await p.chromium.launch(
            headless=True
        )


        page = await browser.new_page()



        for task in tasks:

            await process(
                task,
                page
            )



        await browser.close()




def main(payload=None):

    asyncio.run(
        run_scraper()
    )



def run(payload=None):

    main(payload)



if __name__=="__main__":

    main()