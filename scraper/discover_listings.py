import asyncio
import json
import os
import random
from playwright.async_api import async_playwright
from sqlalchemy import create_engine, text

# Contra Costa ZIP Codes
CONTRA_COSTA_ZIPS = [
    "94506", "94507", "94509", "94511", "94513", "94514", "94517", "94518", 
    "94519", "94520", "94521", "94523", "94525", "94526", "94528", "94530", 
    "94531", "94547", "94549", "94553", "94556", "94561", "94563", "94564", 
    "94565", "94582", "94583", "94595", "94596", "94597", "94598", "94801", 
    "94803", "94804", "94806"
]

DATABASE_URL = os.environ.get('DATABASE_URL', "").replace("postgres://", "postgresql://", 1)
engine = create_engine(DATABASE_URL)

async def human_pause(min_sec=10, max_sec=25):
    await asyncio.sleep(random.uniform(min_sec, max_sec))

async def discover_listings():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Randomizing viewport size helps reduce "bot" fingerprinting
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 800}
        )
        page = await context.new_page()
        
        for zip_code in CONTRA_COSTA_ZIPS:
            search_url = f"https://www.redfin.com/zipcode/{zip_code}"
            print(f"-> Exploring: {search_url}")
            
            try:
                # 1. Navigate and wait for basic load
                await page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
                
                # 2. Sequential scrolling to trigger lazy loading
                for _ in range(5):
                    await page.mouse.wheel(0, 800)
                    await asyncio.sleep(1.5)
                
                # 3. Flexible wait: Don't just wait for one class, wait for common listing markers
                # Redfin uses several classes for cards; we check for any of them.
                try:
                    await page.wait_for_selector(".homes-summary-item, .link-to-more-details", timeout=15000)
                except:
                    print(f"Warning: No explicit cards found for {zip_code}, proceeding with raw link extraction.")
                
                # 4. Extract all links that lead to a '/home/' URL (the canonical Redfin listing pattern)
                links = await page.eval_on_selector_all(
                    "a[href*='/home/']", 
                    "elements => elements.map(e => e.href)"
                )
                
                # Deduplicate and filter (Redfin often uses absolute URLs)
                unique_links = list(set([l for l in links if "/home/" in l]))
                print(f"Found {len(unique_links)} listings in {zip_code}")
                
                # 5. Insert into DB
                with engine.begin() as conn:
                    for url in unique_links:
                        # Ensure we don't insert redundant tasks
                        payload = json.dumps({"url": url})
                        conn.execute(
                            text("INSERT INTO ai_tasks (status, payload) VALUES ('pending', :payload) ON CONFLICT DO NOTHING"),
                            {"payload": payload}
                        )
                
                await human_pause()
                
            except Exception as e:
                print(f"Failed to scrape {zip_code}: {e}")
                # If blocked, increase wait time significantly
                await human_pause(60, 120)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(discover_listings())