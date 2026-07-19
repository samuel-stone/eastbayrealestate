import os
import time
import pandas as pd
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

# Safely get and fix the Database URL
db_url = os.environ.get("DATABASE_URL", "")
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

engine = create_engine(db_url)
TABLE_NAME = "leads_sandbox"

def enrich_address(page, address):
    search_query = address.replace(" ", "+")
    print(f"Navigating to Redfin for: {address}")
    
    try:
        page.goto(f"https://www.redfin.com/stingray/do/lookup-location?location={search_query}")
        page.wait_for_selector(".summary-field", timeout=10000)
        
        price = page.inner_text(".summary-field .price") if page.query_selector(".summary-field .price") else "N/A"
        status = page.inner_text(".home-status-indicator") if page.query_selector(".home-status-indicator") else "Off-Market"
    except Exception as e:
        print(f"Could not extract data for {address}: {e}")
        price, status = "Error", "Error"
        
    return {"address": address, "price": price, "status": status}

def main():
    print("Initializing stealth browser bypass for Redfin...")
    
    try:
        df = pd.read_csv('adu_prospect_list.csv')
    except FileNotFoundError:
        print("Error: adu_prospect_list.csv not found. Create a test file or pull from DB.")
        return

    # NEW V2 SYNTAX: Wrap sync_playwright() with Stealth().use_sync()
    with Stealth().use_sync(sync_playwright()) as p:
        browser = p.chromium.launch(headless=False, channel="chrome")
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        with engine.connect() as conn:
            for _, row in df.head(5).iterrows():
                print(f"[Fetching] {row['address']}...")
                data = enrich_address(page, row['address'])
                
                # Write results directly to Sandbox database
                conn.execute(text(f"""
                    INSERT INTO {TABLE_NAME} (address, lead_rating, last_notes) 
                    VALUES (:addr, 'C', :notes)
                """), {
                    "addr": data["address"], 
                    "notes": f"Price: {data['price']}, Status: {data['status']}"
                })
                conn.commit()
                
                time.sleep(3) # Human delay
                
        browser.close()
        print("Scrape complete. Sandbox database updated.")

if __name__ == "__main__":
    main()