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
        print(f"[!] Queue update failed: {e}")

    finally:
        cur.close()
        conn.close()


async def process(task, page):
    task_id = task["id"]
    url = task["url"]

    if "redfin.com" not in url:
        print(f"[!] Skipping non-Redfin URL: {url}")
        update_queue_status(
            task_id,
            "failed",
            "Non-Redfin URL"
        )
        return

    print(f"\nTASK {task_id}")
    print(f"URL: {url}")

    # Exponential backoff retry loop for resilient scraping
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            response = await page.goto(
                url,
                timeout=60000,
                wait_until="domcontentloaded"
            )
            
            if response and response.status in [403, 429]:
                raise Exception(f"Blocked with status {response.status}")

            await asyncio.sleep(random.uniform(3, 5))

            html_content = await page.content()

            data = parse_listing(
                html_content,
                url,
                task["address"]
            )

            if not data:
                print(f"[!] Failed parsing {url}")
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

                conn.commit()
                update_queue_status(task_id, "completed")
                print(f"[+] Task {task_id} completed successfully.")
                return

            except Exception as e:
                print(f"[!] DB Error on task {task_id}: {e}")
                update_queue_status(task_id, "failed", f"DB insert error: {e}")
                return
            finally:
                cur.close()
                conn.close()

        except Exception as e:
            print(f"[!] Attempt {attempt} failed for task {task_id}: {e}")
            if attempt == max_retries:
                update_queue_status(task_id, "failed", str(e))
            else:
                # Exponential backoff sleep before retrying
                sleep_time = 2 ** attempt + random.uniform(1, 3)
                await asyncio.sleep(sleep_time)


async def run_scraper():
    tasks = get_tasks()
    if not tasks:
        print("[*] No queued Redfin tasks found.")
        return

    # List of common user agents to diversify fingerprinting
    user_agents = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15"
    ]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=random.choice(user_agents)
        )
        page = await context.new_page()

        for task in tasks:
            await process(task, page)

        await browser.close()


def main(payload=None):
    """Main execution entrypoint called by task_registry.py"""
    print("[Pipeline] Starting scrape_redfin")
    asyncio.run(run_scraper())


def run(payload=None):
    """Alias for main() to support legacy calls if any"""
    main(payload)


if __name__ == "__main__":
    main()