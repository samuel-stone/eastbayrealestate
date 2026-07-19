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
        target_url = "https://www.redfin.com/neighborhood/11198/CA/Walnut-Creek/Rossmoor"        
        print(f"Navigating to {target_url}...")
        
        try:
            page.goto(target_url)
            
            # Wait for the property cards to load on the screen
            print("Waiting for property cards to render...")
            page.wait_for_selector('.HomeCardContainer, .v2-interactive, .homecards', timeout=10000) 
            page.wait_for_timeout(3000) # Give it an extra 3 seconds for prices to populate
            
            print("Extracting property data...")
            # Grab all the property cards on the first page
            cards = page.query_selector_all('.HomeCardContainer, .bottomV2')
            
            extracted_count = 0
            with engine.connect() as conn:
                # Loop through the first 10 cards we find
                for card in cards[:10]:
                    try:
                        # Extract the address and price (handling Redfin's common CSS classes)
                        addr_element = card.query_selector('.bp-Homecard__Address, .address')
                        price_element = card.query_selector('.bp-Homecard__Price, .homecardV2Price')
                        
                        if addr_element:
                            address = addr_element.inner_text().strip()
                            price = price_element.inner_text().strip() if price_element else "Price N/A"
                            
                            # Insert the REAL data into the sandbox
                            conn.execute(text(f"""
                                INSERT INTO {TABLE_NAME} (address, lead_rating, last_notes) 
                                VALUES (:addr, 'B', :notes)
                            """), {"addr": address, "notes": f"Rossmoor Scrape - {price}"})
                            extracted_count += 1
                    except Exception as e:
                        continue # Skip if a card is formatted weirdly
                        
                conn.commit()
                
            print(f"Success! Extracted {extracted_count} real properties to the sandbox.")
            
        except Exception as e:
            print(f"Scrape failed: {e}")
            
        finally:
            browser.close()

if __name__ == "__main__":
    run_scraper()