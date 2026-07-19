import re
import asyncio
import json
import os
import sys
import random
from playwright.async_api import async_playwright
from sqlalchemy import create_engine, text

# --- CONFIGURATION ---
DATABASE_URL = os.environ.get('DATABASE_URL', "").replace("postgres://", "postgresql://", 1)
if not DATABASE_URL:
    print("CRITICAL: DATABASE_URL environment variable is not set.")
    sys.exit(1)

engine = create_engine(DATABASE_URL)

async def save_to_sandbox(lead):
    insert_query = text("""
        INSERT INTO leads_sandbox 
        (address, price, beds, baths, sqft, property_type, last_source_url, last_notes)
        VALUES (:address, :price, :beds, :baths, :sqft, :ptype, :url, :notes)
    """)
    with engine.begin() as conn:
        conn.execute(insert_query, {
            "address": "Parsed from Page",
            "price": float(lead["price"]) if lead.get("price") else None,
            "beds": float(lead["beds"]) if lead.get("beds") else None,
            "baths": float(lead["baths"]) if lead.get("baths") else None,
            "sqft": float(lead["sqft"]) if lead.get("sqft") else None,
            "ptype": "Residential",
            "url": lead.get("url"),
            "notes": "v3.3 Worker Scraper"
        })

async def process_task(page, task):
    try:
        payload = json.loads(task.payload) if isinstance(task.payload, str) else task.payload
        url = payload.get("url")
        print(f"-> Processing: {url}")
        
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(random.uniform(3, 6)) 
        
        full_text = await page.evaluate("document.body.innerText")
        
        price_m = re.search(r'\$([\d,]+)', full_text)
        beds_m = re.search(r'([\d\.]+)\s*Bed', full_text, re.IGNORECASE)
        baths_m = re.search(r'([\d\.]+)\s*Bath', full_text, re.IGNORECASE)
        sqft_m = re.search(r'([\d,]+)\s*Sq\.?\s*Ft', full_text, re.IGNORECASE)
        
        data = {
            "price": price_m.group(1).replace(',', '') if price_m else None,
            "beds": beds_m.group(1) if beds_m else None,
            "baths": baths_m.group(1) if baths_m else None,
            "sqft": sqft_m.group(1).replace(',', '') if sqft_m else None,
            "url": url
        }
        
        await save_to_sandbox(data)
        
        with engine.begin() as conn:
            conn.execute(text("UPDATE ai_tasks SET status = 'completed' WHERE id = :id"), {"id": task.id})
            
    except Exception as e:
        print(f"Extraction failed for task {task.id}: {e}")
        with engine.begin() as conn:
            conn.execute(text("UPDATE ai_tasks SET status = 'failed' WHERE id = :id"), {"id": task.id})

async def run_worker():
    print("Starting Worker Scraper batch...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36")
        page = await context.new_page()
        
        with engine.begin() as conn:
            # Process one batch of 20
            tasks = conn.execute(text("SELECT id, payload FROM ai_tasks WHERE status = 'pending' LIMIT 20;")).fetchall()
        
        if not tasks:
            print("No pending tasks found. Exiting.")
            return
        
        for task in tasks:
            await process_task(page, task)
            await asyncio.sleep(random.uniform(5, 10)) 
        
        await browser.close()
    print("Batch complete. Exiting.")

if __name__ == "__main__":
    asyncio.run(run_worker())