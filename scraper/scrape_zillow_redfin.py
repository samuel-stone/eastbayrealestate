import time
import json
import os
from playwright.sync_api import sync_playwright

def run_scraper():
    print("Initializing headless browser bypass for Zillow/Redfin...")
    
    captured_data = []

    def handle_response(response):
        # Target specific GraphQL or API endpoints that return property data
        if "graphql" in response.url or "api/" in response.url:
            try:
                if response.status == 200:
                    data = response.json()
                    captured_data.append(data)
                    print(f"Intercepted payload from: {response.url.split('?')[0]}")
            except Exception:
                pass

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = context.new_page()
        
        # Set a slightly longer structural timeout just in case, but change wait_until
        page.set_default_timeout(45000)
        page.on("response", handle_response)
        
        print("Navigating to target area...")
        # Changing from 'networkidle' to 'load' to avoid analytics script loops
        page.goto("https://www.redfin.com/city/16548/CA/Rossmoor", wait_until="load")
        
        print("Page loaded. Executing stealth scrolling to trigger data payloads...")
        # Give the page a moment to settle
        time.sleep(3)
        
        # Smooth scrolling simulation
        for i in range(3):
            page.mouse.wheel(0, 800)
            time.sleep(2)
            
        print(f"Data extraction complete. Captured {len(captured_data)} raw payloads.")
        
        os.makedirs("data", exist_ok=True)
        with open("data/rossmore_raw_payloads.json", "w") as f:
            json.dump(captured_data, f, indent=2)
            
        print("Saved payloads to data/rossmore_raw_payloads.json")
        browser.close()

if __name__ == "__main__":
    run_scraper()
