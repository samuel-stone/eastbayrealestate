import os
import requests
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

# Safely get and fix the Database URL for SQLAlchemy
db_url = os.environ.get("DATABASE_URL", "")
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

engine = create_engine(db_url)
TABLE_NAME = "scraped_property_data_sandbox"

API_URL = "https://danvilleca-energovpub.tylerhost.net/apps/selfservice/api/energov/search/search"

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
    
    print("Initializing Danville scraper with Session priming...")
    session = requests.Session()
    
    # Prime the cookies by hitting the homepage first
    session.get("https://danvilleca-energovpub.tylerhost.net/Apps/SelfService/", headers=HEADERS)
    
    print("Sending authenticated request to Danville API...")
    try:
        response = session.post(API_URL, json=payload, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        
        results = data.get('Result', []) # EnerGov sometimes uses 'Result' or 'Results'
        if not results and 'Results' in data:
            results = data['Results']
            
        print(f"Success! Received {len(results)} records.")
        
        # Map to DB Sandbox
        with engine.connect() as conn:
            for item in results:
                # EnerGov keys vary, often it's 'Address' or 'MainParcel'
                address = item.get('Address', item.get('AddressLine1', 'Unknown Address'))
                if address and address != 'Unknown Address':
                    conn.execute(text(f"""
                        INSERT INTO {TABLE_NAME} (property_address, category, created_at)
                        VALUES (:addr, 'Danville_Permit', NOW())
                    """), {"addr": address})
            conn.commit()
        print("Sandbox database updated successfully.")
        
    except requests.exceptions.HTTPError as e:
        print(f"Error: {e}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Database error: {e}")

if __name__ == "__main__":
    scrape_danville()