import re
import asyncio
import json
import os
from playwright.async_api import async_playwright
from sqlalchemy import create_engine, text

# Database Setup
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://user:pass@localhost:5432/db')
engine = create_engine(DATABASE_URL.replace('postgres://', 'postgresql://', 1))

async def save_to_sandbox(lead):
    """Inserts a single scraped lead into the sandbox."""
    insert_query = text("""
        INSERT INTO leads_sandbox 
        (address, normalized_address, price, beds, baths, sqft, property_type, last_source_url, last_notes)
        VALUES (:address, :normalized, :price, :beds, :baths, :sqft, :ptype, :url, :notes)
    """)
    
    with engine.begin() as conn:
        conn.execute(insert_query, {
            "address": lead.get("address", "Unknown"),
            "normalized": lead.get("address", "Unknown"),
            "price": float(lead["price"]) if lead.get("price") else None,
            "beds": float(lead["beds"]) if lead.get("beds") else None,
            "baths": float(lead["baths"]) if lead.get("baths") else None,
            "sqft": float(lead["sqft"]) if lead.get("sqft") else None,
            "ptype": "Residential",
            "url": lead.get("url"),
            "notes": "v3.0 Sledgehammer"
        })

async def run_scraper():
    # 1. Fetch pending URLs from the ai_tasks queue
    with engine.begin() as conn:
        tasks = conn.execute(text("SELECT id, payload FROM ai_tasks WHERE status = 'pending' LIMIT 50;")).fetchall()
    
    if not tasks:
        print("No pending tasks found.")
        return

    async with async_playwright() as p:
        # Use a real browser context to avoid bot detection
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
        page = await context.new_page()
        
        for task in tasks:
            try:
                payload = json.loads(task.payload) if isinstance(task.payload, str) else task.payload
                url = payload.get("url")
                
                print(f"-> Inspecting: {url}")
                await page.goto(url, wait_until="networkidle", timeout=60000)
                
                # --- SLEDGEHAMMER EXTRACTION ---
                full_text = await page.evaluate("document.body.innerText")
                
                # Regex Extraction
                price_match = re.search(r'\$([\d,]+)', full_text)
                beds_match = re.search(r'([\d\.]+)\s*Bed', full_text, re.IGNORECASE)
                baths_match = re.search(r'([\d\.]+)\s*Bath', full_text, re.IGNORECASE)
                sqft_match = re.search(r'([\d,]+)\s*Sq\.?\s*Ft', full_text, re.IGNORECASE)
                
                data = {
                    "address": "Parsed from Page",
                    "price": price_match.group(1).replace(',', '') if price_match else None,
                    "beds": beds_match.group(1) if beds_match else None,
                    "baths": baths_match.group(1) if baths_match else None,
                    "sqft": sqft_match.group(1).replace(',', '') if sqft_match else None,
                    "url": url
                }
                
                print(f"Extracted: {data}")
                await save_to_sandbox(data)
                
                # 2. Mark task as 'completed'
                with engine.begin() as conn:
                    conn.execute(text("UPDATE ai_tasks SET status = 'completed' WHERE id = :id"), {"id": task.id})
                
            except Exception as e:
                print(f"Extraction failed for task {task.id}: {e}")
                with engine.begin() as conn:
                    conn.execute(text("UPDATE ai_tasks SET status = 'failed' WHERE id = :id"), {"id": task.id})
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_scraper())