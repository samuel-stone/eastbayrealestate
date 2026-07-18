from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def find_permit_link():
    end_date = datetime.now().strftime('%m/%d/%Y')
    start_date = (datetime.now() - timedelta(days=14)).strftime('%m/%d/%Y')
    url = "https://aca-prod.accela.com/WC/Cap/CapHome.aspx?module=Building&TabName=Building"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)')
        page = context.new_page()
        
        page.goto(url)
        page.evaluate(f"document.querySelector('input[id$=\"txtGSStartDate\"]').value = '{start_date}';")
        page.evaluate(f"document.querySelector('input[id$=\"txtGSEndDate\"]').value = '{end_date}';")
        page.locator("a[id$='btnNewSearch']").click()
        
        page.wait_for_selector("table[id$='gdvPermitList']", timeout=15000)
        table_html = page.locator("table[id$='gdvPermitList']").inner_html()
        browser.close()
        
    soup = BeautifulSoup(table_html, 'html.parser')
    
    # Target Row 3 (the first data row)
    first_data_row = soup.find_all('tr')[3]
    
    # Find all anchor tags (links) in that row
    links = first_data_row.find_all('a')
    
    print("\n=== LINKS FOUND IN FIRST DATA ROW ===")
    for a in links:
        print(f"Text: {a.text.strip()}")
        print(f"Href: {a.get('href', 'No href found')}")
        print(f"ID: {a.get('id', 'No ID found')}")
        print("-" * 40)

if __name__ == "__main__":
    find_permit_link()
