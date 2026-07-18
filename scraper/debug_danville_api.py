from playwright.sync_api import sync_playwright
import time

def sniff_danville_api():
    print("Opening Danville's EnerGov portal...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # Listen to network responses and catch the data search
        def handle_response(response):
            # We look for 'api' and 'search' keywords in the network calls
            if "api" in response.url.lower() and "search" in response.url.lower():
                print(f"\n[!] CAUGHT HIDDEN API REQUEST:")
                print(f"URL: {response.url}")
                print(f"METHOD: {response.request.method}")
                print(f"POST DATA: {response.request.post_data}")
                print("-" * 50)
                
        page.on("response", handle_response)
        
        page.goto("https://danvilleca-energovpub.tylerhost.net/Apps/SelfService#/search")
        
        print("\n=== ACTION REQUIRED ===")
        print("1. Click the 'Search' dropdown in the browser and select 'Permit'.")
        print("2. Enter a date range (e.g., last month) and click 'Search'.")
        print("3. Watch this terminal! The API request will appear above.")
        print("========================\n")
        
        time.sleep(60) # You have 60 seconds to perform the search
        browser.close()

if __name__ == "__main__":
    sniff_danville_api()
