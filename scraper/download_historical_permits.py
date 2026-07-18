import os
import time
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.contracosta.ca.gov"
ARCHIVE_URL = f"{BASE_URL}/Archive.aspx?AMID=268"
DOWNLOAD_DIR = "permit_pdfs"

def download_historical_reports(limit=None):
    """
    Scrapes the Contra Costa County archive for ALL permit PDFs.
    """
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
    
    print(f"Fetching archive page: {ARCHIVE_URL}")
    response = requests.get(ARCHIVE_URL, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    links = soup.find_all('a', href=True)
    report_links = []
    
    for a in links:
        href = a['href']
        text = a.text.strip()
        # Look for any report that has "ADID=" and contains the word "Permit"
        if "ADID=" in href and "Permit" in text:
            report_links.append((text, href))
            
    if limit:
        report_links = report_links[:limit]
            
    print(f"Found {len(report_links)} total reports. Starting download...")
    
    for name, href in report_links:
        pdf_url = BASE_URL + "/" + href.lstrip('/') if not href.startswith('http') else href
        # Sanitize the file name
        safe_name = name.replace('/', '-').replace(' ', '_') + ".pdf"
        pdf_path = os.path.join(DOWNLOAD_DIR, safe_name)
        
        if os.path.exists(pdf_path):
            print(f" [SKIP] Already downloaded: {safe_name}")
            continue
            
        print(f" -> Downloading: {name}")
        pdf_resp = requests.get(pdf_url, headers=headers)
        
        if pdf_resp.status_code == 200 and 'application/pdf' in pdf_resp.headers.get('Content-Type', '').lower():
            with open(pdf_path, 'wb') as f:
                f.write(pdf_resp.content)
            print("    Success!")
        else:
            print("    [!] Failed to download or file is not a PDF.")
        
        # 2-second pause to avoid getting blocked by the county server
        time.sleep(2) 

if __name__ == "__main__":
    # limit=None means it will download every single report in the archive
    download_historical_reports(limit=None)
