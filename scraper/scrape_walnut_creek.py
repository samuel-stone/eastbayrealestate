import sys
import os
import psycopg2
from psycopg2.extras import execute_values
import argparse
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scraper.base import BaseScraper

# Connection string for your Aiven PostgreSQL instance
DB_URL = "postgresql://avnadmin:@164.90.155.207:22742/defaultdb?sslmode=require"

TABLE_SELECTOR = "table[id*='gdvPermitList']"

EXTRACT_TABLE_JS = """
(rows) => rows.map(row => {
    const cells = Array.from(row.querySelectorAll('td'));
    return cells.map(c => c.innerText.trim());
})
"""

class WalnutCreekScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.conn = None

    def init_db(self):
        # Connect to Postgres
        self.conn = psycopg2.connect(DB_URL)
        # Note: Table is assumed to already exist via your previous manual migration

    def save_page_records(self, records, page_num):
        captured_at = datetime.now().isoformat()
        rows_to_insert = [
            (r["permit_no"], r["date"], r["type"], r["description"],
             r["status"], r["address"], page_num, captured_at)
            for r in records
        ]
        
        # PostgreSQL Upsert: Skip if permit_no already exists
        query = """
            INSERT INTO walnut_creek_permits
                (permit_no, permit_date, permit_type, description, status, address, page_number, captured_at)
            VALUES %s
            ON CONFLICT (permit_no) DO NOTHING
        """
        with self.conn.cursor() as cur:
            execute_values(cur, query, rows_to_insert)
        self.conn.commit()

    def run_search(self, days_back=730, max_pages=None):
        start_date = (datetime.now() - timedelta(days=days_back)).strftime('%m/%d/%Y')
        end_date = datetime.now().strftime('%m/%d/%Y')
        search_url = "https://aca-prod.accela.com/WC/Cap/CapHome.aspx?module=Building&TabName=Building"

        self.page.goto(search_url)
        self.page.wait_for_load_state("networkidle")

        self.log_status("Setting dates and triggering search...")
        self.page.evaluate(f"""
            const start = document.querySelector("input[id$='txtGSStartDate']");
            const end = document.querySelector("input[id$='txtGSEndDate']");
            start.value = '{start_date}'; end.value = '{end_date}';
            document.querySelector("a[id$='btnNewSearch']").click();
        """)
        self.page.wait_for_load_state("networkidle")

        # --- RESUME LOGIC ---
        with self.conn.cursor() as cur:
            cur.execute("SELECT MAX(page_number) FROM walnut_creek_permits")
            res = cur.fetchone()
            page_num = res[0] if res and res[0] else 1
        
        if page_num > 1:
            self.log_status(f"Resuming at page {page_num}...")
            self.page.evaluate(f"__doPostBack('ctl00$PlaceHolderMain$dgvPermitList$gdvPermitList', 'Page${page_num}')")
            self.page.wait_for_load_state("networkidle")
            self.page.wait_for_timeout(3000)

        total_captured = 0
        next_link = self.page.locator("a:has-text('Next >')")

        while True:
            if max_pages and page_num > max_pages:
                break
            
            try:
                self.page.wait_for_selector(TABLE_SELECTOR, timeout=60000)
            except Exception:
                break

            raw_rows = self.page.eval_on_selector_all(f"{TABLE_SELECTOR} tr", EXTRACT_TABLE_JS)
            page_records = [
                {"date": d[1], "permit_no": d[2], "type": d[3], "description": d[4], "status": d[5], "address": d[8]}
                for d in raw_rows if len(d) > 5 and d[0] != 'Date' # Skip header
            ]

            self.save_page_records(page_records, page_num)
            total_captured += len(page_records)
            self.log_status(f"Page {page_num}: saved {len(page_records)} permits.")

            if next_link.count() > 0 and next_link.first.is_visible():
                next_link.first.click()
                self.page.wait_for_load_state("networkidle")
                page_num += 1
            else:
                break

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--days-back", type=int, default=730)
    parser.add_argument("--max-pages", type=int, default=None)
    parser.add_argument("--headed", action="store_true")
    args = parser.parse_args()

    scraper = WalnutCreekScraper()
    try:
        scraper.init_db()
        scraper.start_browser(headless=not args.headed)
        scraper.run_search(days_back=args.days_back, max_pages=args.max_pages)
    finally:
        if scraper.conn: scraper.conn.close()
        scraper.close()