import sys
import os
import sqlite3
import argparse
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scraper.base import BaseScraper

TABLE_SELECTOR = "table[id*='gdvPermitList']"

# Extracts ALL row/cell text for the whole table in a single browser round-trip.
# This creates zero Playwright ElementHandles, which is what was leaking memory
# in the old per-row / per-cell query_selector_all() + inner_text() version.
EXTRACT_TABLE_JS = """
(rows) => rows.map(row => {
    const cells = Array.from(row.querySelectorAll('td'));
    return cells.map(c => c.innerText.trim());
})
"""


class WalnutCreekScraper(BaseScraper):
    def __init__(self, db_path='scraper/output/leads.sqlite3'):
        super().__init__(db_path=db_path)
        self.conn = None

    def init_db(self):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS walnut_creek_permits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                permit_no TEXT UNIQUE,
                permit_date TEXT,
                permit_type TEXT,
                description TEXT,
                status TEXT,
                address TEXT,
                page_number INTEGER,
                captured_at TEXT
            )
        """)
        self.conn.commit()

    def save_page_records(self, records, page_num):
        captured_at = datetime.now().isoformat()
        rows_to_insert = [
            (r["permit_no"], r["date"], r["type"], r["description"],
             r["status"], r["address"], page_num, captured_at)
            for r in records
        ]
        # INSERT OR IGNORE: permit_no is UNIQUE, so re-running the scraper
        # after a crash safely skips permits already captured -- no dupes,
        # nothing lost, no need to track/resume a specific page number.
        self.conn.executemany("""
            INSERT OR IGNORE INTO walnut_creek_permits
                (permit_no, permit_date, permit_type, description, status, address, page_number, captured_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, rows_to_insert)
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

        # --- RESUME LOGIC START ---
        # 1. Determine resume page from DB
        cursor = self.conn.execute("SELECT MAX(page_number) FROM walnut_creek_permits")
        max_db_page = cursor.fetchone()[0]
        page_num = max_db_page if max_db_page else 1
        
        # 2. Jump to the resume page if greater than 1
        if page_num > 1:
            self.log_status(f"Database check complete. Resuming directly at page {page_num}...")
            # Trigger the ASP.NET postback directly, skipping previous pages
            # Note: Ensure this ID matches your specific target grid in the DOM
            self.page.evaluate(f"__doPostBack('ctl00$PlaceHolderMain$dgvPermitList$gdvPermitList', 'Page${page_num}')")
            self.page.wait_for_load_state("networkidle")
            self.page.wait_for_timeout(3000) # Allow DOM grid hydration
        # --- RESUME LOGIC END ---

        total_captured = 0
        next_link = self.page.locator("a:has-text('Next >')")

        while True:
            if max_pages and page_num > max_pages:
                self.log_status(f"Reached --max-pages limit ({max_pages}). Stopping early.")
                break

            self.log_status(f"Scraping page {page_num}...")
            
            try:
                self.page.wait_for_selector(TABLE_SELECTOR, timeout=60000)
            except Exception:
                self.log_status(f"Table not found on page {page_num}. Ending scrape.")
                break

            # Single round-trip, no ElementHandles created.
            raw_rows = self.page.eval_on_selector_all(f"{TABLE_SELECTOR} tr", EXTRACT_TABLE_JS)

            page_records = []
            for i, data in enumerate(raw_rows):
                if i < 2:
                    continue
                if len(data) > 5:
                    page_records.append({
                        "date": data[1],
                        "permit_no": data[2],
                        "type": data[3],
                        "description": data[4],
                        "status": data[5],
                        "address": data[8],
                    })

            self.save_page_records(page_records, page_num)
            total_captured += len(page_records)
            self.log_status(f"Page {page_num}: saved {len(page_records)} permits (total this session: {total_captured})")

            # Safe Next Button Navigation
            if next_link.count() > 0 and next_link.first.is_visible():
                self.log_status("Moving to next page...")
                try:
                    next_link.first.click(timeout=15000)
                    self.page.wait_for_load_state("networkidle", timeout=45000)
                    page_num += 1
                except Exception as e:
                    self.log_status(f"Could not transition to next page due to timeout or error: {e}")
                    self.log_status("Saving progress and shutting down safely.")
                    break
            else:
                self.log_status("No more pages found.")
                break

        self.log_status(f"Done. Captured {total_captured} permits this session.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape Walnut Creek building permits (Accela portal)")
    parser.add_argument("--days-back", type=int, default=730, help="How many days back to search (default 730)")
    parser.add_argument("--max-pages", type=int, default=None,
                         help="Stop after N pages -- use this to test the fix on a small run before doing a full scrape")
    parser.add_argument("--headed", action="store_true", help="Show the browser window (default: headless, which also uses less memory)")
    args = parser.parse_args()

    scraper = WalnutCreekScraper()
    try:
        scraper.init_db()
        scraper.start_browser(headless=not args.headed)
        scraper.run_search(days_back=args.days_back, max_pages=args.max_pages)
    except Exception as e:
        print(f"[Fatal Error] {e}")
    finally:
        if scraper.conn:
            scraper.conn.close()
        scraper.close()