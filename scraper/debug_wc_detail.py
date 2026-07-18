from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re

def debug_first_permit():
    end_date = datetime.now().strftime('%m/%d/%Y')
    start_date = (datetime.now() - timedelta(days=14)).strftime('%m/%d/%Y')
    url = "https://aca-prod.accela.com/WC/Cap/CapHome.aspx?module=Building&TabName=Building"
    
    with sync_playwright() as p:
        # Running headless for speed
        browser = p.chromium.launch(headless=True) 
        context = browser.new_context(user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)')
        page = context.new_page()
        
        print("Opening portal and searching...")
        page.goto(url)
        page.evaluate(f"document.querySelector('input[id$=\"txtGSStartDate\"]').value = '{start_date}';")
        page.evaluate(f"document.querySelector('input[id$=\"txtGSEndDate\"]').value = '{end_date}';")
        page.locator("a[id$='btnNewSearch']").click()
        
        print("Waiting for grid...")
        page.wait_for_selector("table[id$='gdvPermitList']", timeout=15000)
        
        print("Clicking into the first permit...")
        # Click the first link in the first data row
        page.locator("table[id$='gdvPermitList'] tr").nth(1).locator("a").first.click()
        
        # Wait for the detail page to load ('Record Details' is standard across Accela)
        page.wait_for_selector("span:has-text('Record Details')", timeout=15000)
        
        html = page.content()
        browser.close()
        
    print("\n=== SCANNING DETAIL PAGE FOR LOCATION INFO ===")
    soup = BeautifulSoup(html, 'html.parser')
    
    for span in soup.find_all('span'):
        span_id = span.get('id', '')
        text = span.text.strip()
        
        # Look for common Accela IDs for Address or Parcel
        if 'Address' in span_id or 'Parcel' in span_id or 'WorkLocation' in span_id:
            if text:
                print(f"Found via ID [{span_id}]: {text}")
        elif re.match(r'^\d+\s+[A-Za-z]+', text) and len(text) > 10 and len(text) < 50:
             print(f"Possible Address Text: {text}")

if __name__ == "__main__":
    debug_first_permit()
