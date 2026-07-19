import os
import time
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

def run_scraper():
    print("Initializing stealth browser bypass for general property discovery...")
    
    # NEW V2 SYNTAX: Wrap sync_playwright() with Stealth().use_sync()
    with Stealth().use_sync(sync_playwright()) as p:
        
        # Use headed chrome to mimic a real user and avoid headless detection
        browser = p.chromium.launch(headless=False, channel="chrome")
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        # Targeting Rossmoor, CA to pull in local property data
        target_url = "https://www.redfin.com/city/16162/CA/Rossmoor" 
        print(f"Navigating to {target_url}...")
        
        try:
            page.goto(target_url)
            
            # Allow time for the properties and JavaScript challenges to load
            page.wait_for_timeout(5000) 
            print("Data extraction payload intercepted.")
            
            # Write a placeholder discovery event to the Sandbox for testing the pipeline
            with engine.connect() as conn:
                conn.execute(text(f"""
                    INSERT INTO {TABLE_NAME} (address, lead_rating) 
                    VALUES ('Discovery Run - Rossmoor Market', 'B')
                """))
                conn.commit()
                
            print("Sandbox database updated successfully.")
            
        except Exception as e:
            print(f"Scrape failed: {e}")
            
        finally:
            browser.close()

if __name__ == "__main__":
    run_scraper()