import pandas as pd
from playwright.sync_api import sync_playwright
import time

def enrich_address(page, address):
    # Navigate to Redfin Search
    # Redfin search URL format is very predictable
    search_query = address.replace(" ", "+")
    page.goto(f"https://www.redfin.com/stingray/do/lookup-location?location={search_query}")
    
    # Wait for the page to load the property summary
    page.wait_for_selector(".summary-field")
    
    # Extract data using CSS selectors
    price = page.inner_text(".summary-field .price") if page.query_selector(".summary-field .price") else "N/A"
    status = page.inner_text(".home-status-indicator") if page.query_selector(".home-status-indicator") else "Off-Market"
    
    return {"address": address, "price": price, "status": status}

def main():
    df = pd.read_csv('adu_prospect_list.csv')
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        results = []
        for _, row in df.head(10).iterrows():
            print(f"[Fetching] {row['address']}...")
            data = enrich_address(page, row['address'])
            results.append(data)
            time.sleep(2) # Be polite to the server
            
        browser.close()
        # Save enriched data
        pd.DataFrame(results).to_csv('enriched_leads.csv', index=False)

if __name__ == "__main__":
    main()
