import os
import time
import glob
import pandas as pd
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

db_url = os.environ.get("DATABASE_URL", "")
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

engine = create_engine(db_url)
TABLE_NAME = "leads_sandbox"
TARGET_DIR = "target_lists"

def enrich_address(page, address):
    search_query = address.replace(" ", "+")
    
    try:
        page.goto(f"https://www.redfin.com/stingray/do/lookup-location?location={search_query}")
        page.wait_for_selector(".summary-field", timeout=10000)
        
        raw_price = page.inner_text(".summary-field .price") if page.query_selector(".summary-field .price") else None
        status = page.inner_text(".home-status-indicator") if page.query_selector(".home-status-indicator") else "Off-Market"
        
        # Clean the price string securely
        price = int(''.join(filter(str.isdigit, raw_price))) if raw_price else None
    except Exception as e:
        print(f"Extraction error for {address}: {e}")
        price, status = None, "Error"
        
    return {"address": address, "price": price, "status": status}

def main():
    csv_files = glob.glob(f"{TARGET_DIR}/*.csv")
    if not csv_files:
        print("No target lists found.")
        return

    # Grab proxy credentials from Railway environment variables
    PROXY_SERVER = os.environ.get("PROXY_SERVER")     
    PROXY_USERNAME = os.environ.get("PROXY_USERNAME")
    PROXY_PASSWORD = os.environ.get("PROXY_PASSWORD")

    launch_args = {
        "headless": True,
        "args": [
            "--no-sandbox", 
            "--disable-setuid-sandbox", 
            "--disable-dev-shm-usage"
        ]
    }

    if PROXY_SERVER and PROXY_USERNAME and PROXY_PASSWORD:
        launch_args["proxy"] = {
            "server": PROXY_SERVER,
            "username": PROXY_USERNAME,
            "password": PROXY_PASSWORD
        }
        print("Residential proxy routing engaged for enrichment.")

    with Stealth().use_sync(sync_playwright()) as p:
        browser = p.chromium.launch(**launch_args)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        for file in csv_files:
            file_name = os.path.basename(file)
            df = pd.read_csv(file)
            
            if 'address' not in df.columns:
                continue

            for _, row in df.iterrows():
                data = enrich_address(page, row['address'])
                
                with engine.begin() as conn:
                    conn.execute(text(f"""
                        INSERT INTO {TABLE_NAME} (address, lead_rating, price, last_notes) 
                        VALUES (:addr, 'C', :price, :notes)
                    """), {
                        "addr": data["address"], 
                        "price": data["price"],
                        "notes": f"Status: {data['status']} (List: {file_name})"
                    })
                
                time.sleep(3)
                
        browser.close()

if __name__ == "__main__":
    os.makedirs(TARGET_DIR, exist_ok=True)
    main()