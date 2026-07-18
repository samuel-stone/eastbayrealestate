import requests
from bs4 import BeautifulSoup

ARCHIVE_URL = "https://www.contracosta.ca.gov/Archive.aspx?AMID=268"
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
soup = BeautifulSoup(requests.get(ARCHIVE_URL, headers=headers).text, 'html.parser')

for a in soup.find_all('a', href=True):
    if "ADID=" in a['href'] and "Unincorporated" in a.text:
        detail_url = "https://www.contracosta.ca.gov/" + a['href'].lstrip('/') if not a['href'].startswith('http') else a['href']
        print(f"Detail URL: {detail_url}")
        
        detail_soup = BeautifulSoup(requests.get(detail_url, headers=headers).text, 'html.parser')
        print("\n=== ALL LINKS ON DETAIL PAGE ===")
        for link in detail_soup.find_all('a', href=True):
            print(f" - Text: {link.text.strip()} | Href: {link['href']}")
        break
