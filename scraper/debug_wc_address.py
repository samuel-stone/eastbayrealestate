from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re

def check_address_field():
    # The exact detail URL we just extracted
    url = "https://aca-prod.accela.com/WC/Cap/CapDetail.aspx?Module=Building&TabName=Building&capID1=26CAP&capID2=00000&capID3=003ID&agencyCode=WC"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)')
        page = context.new_page()
        
        print("Loading permit detail page...")
        page.goto(url)
        page.wait_for_load_state('networkidle')
        
        html = page.content()
        browser.close()
        
    soup = BeautifulSoup(html, 'html.parser')
    print("\n=== SCANNING DETAIL PAGE FOR LOCATION DATA ===")
    
    # Accela usually stores addresses in spans with 'Address' or 'WorkLocation' in the ID
    for span in soup.find_all('span'):
        id_str = span.get('id', '')
        if 'Address' in id_str or 'WorkLocation' in id_str or 'Parcel' in id_str:
            text = span.get_text(separator=" ", strip=True)
            if text:
                print(f"Found Match [ID: {id_str}]: {text}")

if __name__ == "__main__":
    check_address_field()
