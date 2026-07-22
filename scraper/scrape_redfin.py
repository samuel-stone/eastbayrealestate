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
            LIMIT 5;
        """)

        return cur.fetchall()

    except Exception as e:
        print(f"[!] Error fetching tasks: {e}")
        return []

    finally:
        cur.close()
        conn.close()

async def process(task, page):

    task_id = task["id"]
    url = task["url"]

    if url.endswith(".zip"):
        print(f"[!] Skipping non-Redfin URL: {url}")
        return

    print(f"\nTASK: {task_id} | URL: {url}")
    print("OPENING PAGE")

    try:
        await page.goto(
            url,
            timeout=60000,
            wait_until="domcontentloaded"
        )

        await asyncio.sleep(random.uniform(2, 4))

        html_content = await page.content()

       data = parse_listing(
            html_content,
            url,
            task["address"]
)

        if not data:
            print(f"[!] Failed parsing {url}")
            return


        conn = get_db_connection()
        cur = conn.cursor()

        try:

            cur.execute("""
                INSERT INTO properties (
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
                VALUES (
                    %s,%s,%s,%s,%s,%s,%s,%s,%s,NOW()
                )

                ON CONFLICT (address)
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

                data.get("address"),
                data.get("url"),
                data.get("price"),
                data.get("beds"),
                data.get("baths"),
                data.get("sqft"),
                data.get("dom"),
                data.get("price_drops"),
                data.get("is_fixer")

            ))


            cur.execute("""
                UPDATE leads
                SET property_id = (
                    SELECT id
                    FROM properties
                    WHERE address = %s
                )
                WHERE id = %s;
            """, (
                data.get("address"),
                task_id
            ))


            conn.commit()

            print(
                f"[+] Saved property: {data.get('address')}"
            )


        except Exception as db_error:

            conn.rollback()

            print(
                f"[-] Database error: {db_error}"
            )


        finally:

            cur.close()
            conn.close()


    except Exception as e:

        print(
            f"[!] Error processing {url}: {e}"
        )


async def async_main():

    print("Starting Redfin Worker v9.0")

    tasks = get_tasks()

    print(
        "Pending:",
        len(tasks)
    )


    if not tasks:

        print("Complete")
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
                "width":1280,
                "height":900
            },

            user_agent=(
                "Mozilla/5.0 "
                "(Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/127 Safari/537.36"
            )
        )


        page = await context.new_page()


        for task in tasks:

            await process(
                task,
                page
            )

            await asyncio.sleep(
                random.uniform(3,6)
            )


        await browser.close()



def main():

    asyncio.run(
        async_main()
    )


if __name__ == "__main__":

    print("CALLING MAIN")

    main()