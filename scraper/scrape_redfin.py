import asyncio
import os
import random
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

def save_property(data):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO properties (
                address, url, price, beds, baths, sqft, dom, price_drops, is_fixer, last_scraped_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
            )
            ON CONFLICT(address) DO UPDATE SET
                url = EXCLUDED.url,
                price = EXCLUDED.price,
                beds = EXCLUDED.beds,
                baths = EXCLUDED.baths,
                sqft = EXCLUDED.sqft,
                dom = EXCLUDED.dom,
                price_drops = EXCLUDED.price_drops,
                is_fixer = EXCLUDED.is_fixer,
                last_scraped_at = NOW()
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
    finally:
        cur.close()
        conn.close()

async def scrape_url(url):
    print("[REDFIN] Scraping listing:", url)
    
    async with async_playwright() as p:
        # Launch with anti-bot arguments
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        # Set a realistic user agent and headers
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9",
            }
        )
        
        page = await context.new_page()
        
        try:
            # Added a 45-second timeout and wrapped in try/except
            await page.goto(
                url,
                timeout=45000,
                wait_until="domcontentloaded"
            )
            
            # Sleep longer to simulate human delay and avoid rate limits
            await asyncio.sleep(random.uniform(4, 8))
            
            html = await page.content()
            data = parse_listing(html, url)
            
            if not data.get("address"):
                raise Exception("Parser returned no address (Possible Captcha/Block)")
            
            save_property(data)
            print(f"[SCRAPER] Saved {data.get('address')}")
            return data
            
        except Exception as e:
            print(f"[SCRAPER] Error processing {url}: {str(e)}")
            raise e
            
        finally:
            await browser.close()

def scrape_listing(url):
    return asyncio.run(scrape_url(url))

def run(payload=None):
    if not payload:
        return None
    url = payload.get("url")
    if not url:
        return None
    return scrape_listing(url)

if __name__ == "__main__":
    run()