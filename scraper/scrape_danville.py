import requests, sqlite3
from datetime import datetime, timedelta

API_URL = "https://danvilleca-energovpub.tylerhost.net/apps/selfservice/api/energov/search/search"

# Add browser-like headers
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "Referer": "https://danvilleca-energovpub.tylerhost.net/Apps/SelfService/",
    "Content-Type": "application/json",
    "Accept": "application/json, text/plain, */*"
}

def scrape_danville():
    payload = {
        "SearchModule": 1,
        "FilterModule": 1,
        "PermitCriteria": {
            "PageNumber": 1,
            "PageSize": 100
        }
    }
    
    print("Sending authenticated request to Danville API...")
    try:
        response = requests.post(API_URL, json=payload, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        print("Success! Data received.")
        # Logic to map to DB will follow once we confirm this header bypass works
    except requests.exceptions.HTTPError as e:
        print(f"Error: {e}")
        print(f"Response: {response.text}")

if __name__ == "__main__":
    scrape_danville()
