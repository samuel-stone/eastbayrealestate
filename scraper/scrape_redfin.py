import asyncio
import random
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from playwright.async_api import async_playwright
from scraper.parse_redfin_html import parse_listing

DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def get_tasks():
    """Fetch queued or pending scraping tasks from the database."""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Fetch tasks that need scraping
        cur.execute("""
            SELECT id, url, address 
            FROM scraped_leads 
            WHERE scraped_at IS NULL 
            LIMIT 5;
        """)
        tasks = cur.fetchall()
        return tasks
    except Exception as e:
        print(f"[!] Error fetching tasks: {e}")
        return []
    finally:
        cur.close()
        conn.close()

async def process(task, page):
    task_id = task["id"]
    url = task["url"]
    print(f"\nTASK: {task_id} | URL: {url}")
    print("OPENING PAGE")

    try:
        await page.goto(url, timeout=60000, wait_until="domcontentloaded")
        await asyncio.sleep(random.uniform(2, 4))
        
        html_content = await page.content()
        
        # Parse data using the modular helper
        data = parse_listing(html_content, url)
        
        if not data:
            print(f"[!] Failed to parse listing data for {url}")
            return

        # Save to database with fallback insert/update logic
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO properties (url, address, price, beds, baths, sqft, scraped_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (url) DO UPDATE SET
                    price = EXCLUDED.price,
                    beds = EXCLUDED.beds,
                    baths = EXCLUDED.baths,
                    sqft = EXCLUDED.sqft,
                    scraped_at = NOW();
            """, (
                data.get("url"),
                data.get("address"),
                data.get("price"),
                data.get("beds"),
                data.get("baths"),
                data.get("sqft")
            ))
            
            # Mark lead as scraped
            cur.execute("""
                UPDATE scraped_leads 
                SET scraped_at = NOW() 
                WHERE id = %s;
            """, (task_id,))
            
            conn.commit()
            print(f"[+] Successfully scraped and saved: {data.get('address')}")
            
        except Exception as db_err:
            conn.rollback()
            # Fallback if ON CONFLICT constraint isn't present yet
            try:
                cur.execute("""
                    INSERT INTO properties (url, address, price, beds, baths, sqft, scraped_at)
                    VALUES (%s, %s, %s, %s, %s, %s, NOW());
                """, (
                    data.get("url"),
                    data.get("address"),
                    data.get("price"),
                    data.get("beds"),
                    data.get("baths"),
                    data.get("sqft")
                ))
                cur.execute("UPDATE scraped_leads SET scraped_at = NOW() WHERE id = %s;", (task_id,))
                conn.commit()
                print(f"[+] Successfully saved (fallback insert) for: {data.get('address')}")
            except Exception as inner_err:
                print(f"[-] Upsert error for {data.get('address', url)}: {inner_err}")
        finally:
            cur.close()
            conn.close()

    except Exception as e:
        print(f"[!] Error processing page {url}: {e}")

async def async_main():
    print("Starting Redfin Worker v8.0")
    tasks = get_tasks()
    print("Pending:", len(tasks))

    if not tasks:
        print("Complete")
        return

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0 Safari/537.36"
        )
        page = await context.new_page()

        for task in tasks:
            await process(task, page)
            await asyncio.sleep(random.uniform(3, 6))

        await browser.close()

def main():
    asyncio.run(async_main())

if __name__ == "__main__":
    print("CALLING MAIN")
    main()