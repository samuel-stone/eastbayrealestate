# scraper/base.py
from playwright.sync_api import sync_playwright

class BaseScraper:
    def __init__(self, db_path='scraper/output/leads.sqlite3'):
        self.db_path = db_path
        self.browser = None
        self.page = None
        self.playwright = None

    def start_browser(self, headless=True):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=headless)
        self.page = self.browser.new_page()

    def log_status(self, message):
        print(f"[Status] {message}")

    def close(self):
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
