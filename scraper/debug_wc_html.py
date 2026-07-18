from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def print_table_structure():
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
        
        # Grab the whole table HTML
        table_html = page.locator("table[id$='gdvPermitList']").inner_html()
        browser.close()
        
    print("\n=== TOP OF THE ACCELA TABLE ===")
    soup = BeautifulSoup(table_html, 'html.parser')
    
    # Print the first 4 rows to see the headers, the summary, and the real data
    for i, tr in enumerate(soup.find_all('tr')[:4]):
        print(f"\n--- ROW {i} ---")
        # Print a condensed version of the row's contents
        print(tr.prettify()[:600].strip())
        if len(tr.prettify()) > 600:
            print("... (truncated)")

if __name__ == "__main__":
    print_table_structure()
