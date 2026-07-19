import os
import time
import requests
from bs4 import BeautifulSoup
from config.config import Registry

# Using the Registry to get cities if needed for future filtering
CONFIG = Registry.load_sources()
DOWNLOAD_DIR = "permit_pdfs"

def download_historical_reports(limit=None):
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
    
    print(f"Fetching archives...")
    response = requests.get("https://www.contracosta.ca.gov/Archive.aspx?AMID=268", headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    report_links = [(a.text.strip(), a['href']) for a in soup.find_all('a', href=True) if "ADID=" in a['href'] and "Permit" in a.text]
    
    for name, href in report_links[:limit]:
        pdf_url = f"https://www.contracosta.ca.gov/{href.lstrip('/')}"
        safe_name = f"{name.replace('/', '-').replace(' ', '_')}.pdf"
        pdf_path = os.path.join(DOWNLOAD_DIR, safe_name)
        
        if not os.path.exists(pdf_path):
            print(f" -> Downloading: {name}")
            resp = requests.get(pdf_url, headers=headers)
            if resp.status_code == 200:
                with open(pdf_path, 'wb') as f: f.write(resp.content)
            time.sleep(2) 

if __name__ == "__main__":
    download_historical_reports()