import sqlite3, json, re, time
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright

DB_PATH = 'scraper/output/leads.sqlite3'
LEADS_APN_COLUMN = 'parcel_number'

def backfill_walnut_creek(days_back=730):
    start_date = (datetime.now() - timedelta(days=days_back)).strftime('%m/%d/%Y')
    end_date = datetime.now().strftime('%m/%d/%Y')
    search_url = "https://aca-prod.accela.com/WC/Cap/CapHome.aspx?module=Building&TabName=Building"
    
    with sync_playwright() as p:
        # Launch with visible browser to debug why it's missing the inputs
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(search_url)
        
        # Give it a long time to load all frames
        time.sleep(10)
        
        # Use a more aggressive injection that hits ALL frames on the page
        js_injection = f"""
            const allFrames = window.frames;
            let found = false;
            for (let i = 0; i < allFrames.length; i++) {{
                try {{
                    const doc = allFrames[i].document;
                    const start = doc.querySelector("input[id$='txtGSStartDate']");
                    const end = doc.querySelector("input[id$='txtGSEndDate']");
                    if (start && end) {{
                        start.value = '{start_date}';
                        end.value = '{end_date}';
                        doc.querySelector("a[id$='btnNewSearch']").click();
                        found = true;
                        break;
                    }}
                }} catch(e) {{ continue; }}
            }}
            found;
        """
        
        print("Injecting search criteria into frames...")
        page.evaluate(js_injection)
        
        # Wait for the results table specifically
        page.wait_for_selector("table[id$='gdvPermitList']", timeout=40000)
        
        # ... (rest of parsing logic)
        print("Results found! Proceeding with extraction...")
        browser.close()

if __name__ == "__main__":
    backfill_walnut_creek()
