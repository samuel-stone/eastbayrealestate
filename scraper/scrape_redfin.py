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

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("DATABASE_URL missing")
    sys.exit(1)

DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
engine = create_engine(DATABASE_URL)

try:
    # FIXED: Updated 'scripts' to 'scraper' so it finds the file!
    from scraper.parse_redfin_html import parse_listing
except Exception as e:
    print("Parser unavailable:", e)
    parse_listing = None


def get_tasks():
    with engine.begin() as conn:
        return conn.execute(text("""
            SELECT id, payload FROM ai_tasks
            WHERE task_type='scrape_listing' AND status='pending'
            ORDER BY id LIMIT 20
        """)).fetchall()


def update_task(task_id, status):
    with engine.begin() as conn:
        conn.execute(text("UPDATE ai_tasks SET status=:status WHERE id=:id"), {"id": task_id, "status": status})


def address_from_url(url):
    match = re.search(r'/([^/]+)-\d{5}/home', url)
    if not match: return None
    return match.group(1).replace("-", " ").title()


def save_lead(data, url, note):
    address = data.get("address")
    if not address: return
    
    normalized_address = address.strip().lower()
    city = data.get("city", "Walnut Creek") # Defaulting for DB constraints
    
    price_val = data.get("price")
    assessed_value = None
    if price_val:
        cleaned = re.sub(r'[^0-9.]', '', str(price_val))
        if cleaned: assessed_value = float(cleaned)

    try:
        # 1. Upsert into core leads table
        upsert_lead(
            normalized_address=normalized_address,
            city=city,
            address=address,
            parcel_number=data.get("parcel_number"),
            assessed_value=assessed_value,
            status="Active"
        )
        print(f"[+] Upserted core lead: {address}")

        # 2. Extract Lead ID and Upsert to Marketplace Signals table
        with engine.begin() as conn:
            res = conn.execute(text("SELECT id FROM leads WHERE address = :address AND city = :city"), {"address": address, "city": city}).fetchone()
            if res:
                lead_id = res[0]
                dom = data.get("dom", 0)
                price_drops = data.get("price_drops", 0)
                is_fixer = data.get("is_fixer", False)
                score = (price_drops * 25) + (dom // 2)

                conn.execute(text("""
                    INSERT INTO marketplace_signals (lead_id, days_on_market, current_price, price_drop_count, is_fixer_or_tlc, seller_motivation_score, updated_at)
                    VALUES (:lead_id, :dom, :price, :price_drops, :is_fixer, :score, NOW())
                    ON CONFLICT (lead_id) DO UPDATE 
                    SET days_on_market = EXCLUDED.days_on_market,
                        current_price = EXCLUDED.current_price,
                        price_drop_count = EXCLUDED.price_drop_count,
                        is_fixer_or_tlc = EXCLUDED.is_fixer_or_tlc,
                        seller_motivation_score = EXCLUDED.seller_motivation_score,
                        updated_at = NOW();
                """), {
                    "lead_id": lead_id, "dom": dom, "price": assessed_value or 0, 
                    "price_drops": price_drops, "is_fixer": is_fixer, "score": score
                })
                print(f"[+] Upserted motivation signals for {address} (Score: {score})")

    except Exception as e:
        print(f"[-] Upsert error for {address}: {e}")


async def fetch_redfin(page, url):
    print("OPENING PAGE")
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(5000)
    except Exception as e:
        print("PAGE ERROR:", e)
        return None

    html = await page.content()
    if len(html) < 50000 or "Access Denied" in html:
        print("HTML TOO SMALL OR BLOCKED")
        return None
    return html


async def process(task, page):
    task_id, payload = task.id, task.payload
    if isinstance(payload, str):
        payload = json.loads(payload)

    url = payload.get("url")
    print(f"\nTASK: {task_id} | URL: {url}")

    data = {"address": address_from_url(url), "price": None, "beds": None, "baths": None, "sqft": None, "dom": 0, "price_drops": 0, "is_fixer": False}

    html = await fetch_redfin(page, url)
    if not html:
        print("BLOCKED - leaving pending")
        return

    if parse_listing:
        try:
            parsed = parse_listing(html, url)
            if parsed: data.update(parsed)
        except Exception as e:
            print("PARSER ERROR:", e)

    save_lead(data, url, "v8.0 Playwright Redfin scraper")
    update_task(task_id, "completed")


# --------------------------------------------------
# MAIN
# --------------------------------------------------

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

# Synchronous wrapper for task_registry.py compatibility
def main():
    asyncio.run(async_main())

# --------------------------------------------------
# ENTRYPOINT
# --------------------------------------------------

if __name__ == "__main__":
    print("CALLING MAIN")
    main()