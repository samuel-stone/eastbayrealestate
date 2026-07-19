import os
import asyncio
import random
import re
from sqlalchemy import create_engine, text
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

# 1. Database Connection Configuration
db_url = os.environ.get("DATABASE_URL", "")
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

engine = create_engine(db_url)

# 2. Full Contra Costa County Master Zip Code List
CONTRA_COSTA_ZIPS = [
    "94506", "94507", "94509", "94511", "94513", "94514", "94516", 
    "94517", "94518", "94519", "94520", "94521", "94522", "94523", 
    "94524", "94525", "94526", "94527", "94528", "94529", "94530", 
    "94531", "94547", "94548", "94549", "94551", "94553", "94556", 
    "94561", "94563", "94564", "94565", "94569", "94570", "94572", 
    "94575", "94582", "94583", "94595", "94596", "94597", "94598", 
    "94708", "94801", "94802", "94803", "94804", "94805", "94806", 
    "94807", "94808", "94820", "94850"
]

async def scrape_properties():
    all_extracted_leads = []
    
    print("Initializing Stealth browser for deep patient crawl...")
    
    # Grab proxy credentials from Railway environment variables
    PROXY_SERVER = os.environ.get("PROXY_SERVER")     
    PROXY_USERNAME = os.environ.get("PROXY_USERNAME")
    PROXY_PASSWORD = os.environ.get("PROXY_PASSWORD")

    # Base Docker-friendly launch arguments
    launch_args = {
        "headless": True,
        "args": [
            "--no-sandbox", 
            "--disable-setuid-sandbox", 
            "--disable-dev-shm-usage"
        ]
    }

    # Inject proxy configuration if the variables exist in Railway
    if PROXY_SERVER and PROXY_USERNAME and PROXY_PASSWORD:
        launch_args["proxy"] = {
            "server": PROXY_SERVER,
            "username": PROXY_USERNAME,
            "password": PROXY_PASSWORD
        }
        print("Residential proxy routing engaged.")
    else:
        print("Warning: No proxy detected. Using standard datacenter IP.")
    
    # Wrap the async_playwright instance in Stealth
    async with Stealth().use_async(async_playwright()) as p:
        browser = await p.chromium.launch(**launch_args)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        page = await context.new_page()
        
        for zip_code in CONTRA_COSTA_ZIPS:
            page_num = 1
            while True:
                base_url = f"https://www.redfin.com/zipcode/{zip_code}"
                list_url = base_url if page_num == 1 else f"{base_url}/page-{page_num}"
                
                print(f"\n[Scraping] {zip_code} - Page {page_num}...")
                
                try:
                    await page.goto(list_url, wait_until="domcontentloaded")
                    await page.wait_for_timeout(random.randint(4000, 7000))
                except Exception as e:
                    print(f"Failed to load {list_url}: {e}")
                    break
                
                if page_num > 1 and "/page-" not in page.url:
                    break
                
                # 1. Extract individual property links
                property_links = await page.locator("a[href^='/CA/']").evaluate_all(
                    "elements => elements.map(e => e.href)"
                )
                
                property_links = list(set(property_links))
                
                if not property_links:
                    print(f"No more listings found in {zip_code}.")
                    break
                    
                print(f"Discovered {len(property_links)} detail links. Processing slowly...")
                
                # 2. Iterate through home detail pages
                for url in property_links:
                    try:
                        print(f"-> Inspecting: {url}")
                        await page.goto(url, wait_until="domcontentloaded")
                        await page.wait_for_timeout(random.randint(5000, 9500)) 
                        
                        # --- BULLETPROOF REGEX EXTRACTION ---
                        try:
                            # Target the top half of the property page which contains the core stats
                            top_section = await page.locator('.HomeInfo, .home-main-stats-variant, .home-info-v2, .keyDetailsList, header').first.inner_text(timeout=8000)
                            
                            # Price
                            price_match = re.search(r'\$([\d,]+)', top_section)
                            price = int(price_match.group(1).replace(',', '')) if price_match else None
                            
                            # Beds
                            beds_match = re.search(r'([\d\.]+)\s*Beds?', top_section, re.IGNORECASE)
                            beds = float(beds_match.group(1)) if beds_match else None
                            
                            # Baths
                            baths_match = re.search(r'([\d\.]+)\s*Baths?', top_section, re.IGNORECASE)
                            baths = float(baths_match.group(1)) if baths_match else None
                            
                            # Sqft
                            sqft_match = re.search(r'([\d,]+)\s*Sq\.?\s*Ft\.?', top_section, re.IGNORECASE)
                            sqft = float(sqft_match.group(1).replace(',', '')) if sqft_match else None

                        except Exception as e:
                            print(f"Extraction failed for {url}: {e}")
                            price, beds, baths, sqft = None, None, None, None
                            await page.screenshot(path=f"debug_captcha_{zip_code}.png")

                        # Address Extraction
                        try:
                            street = await page.locator('.street-address').first.inner_text()
                            city_state = await page.locator('.dp-subtext').first.inner_text()
                            full_address = f"{street}, {city_state}"
                        except:
                            full_address = f"Unknown Address, {zip_code}"

                        extracted_detail = {
                            "address": full_address, 
                            "price": price, 
                            "beds": beds,
                            "baths": baths,
                            "sqft": sqft,
                            "property_type": "Unknown", 
                            "url": url,
                            "rating": "C"
                        }
                        
                        all_extracted_leads.append(extracted_detail)
                        
                    except Exception as e:
                        print(f"Failed to crawl {url}: {e}")
                        
                page_num += 1
                await page.wait_for_timeout(random.randint(3000, 6000))

        await browser.close()
        return all_extracted_leads

def save_to_sandbox(leads):
    if not leads:
        print("No leads to save.")
        return
        
    print(f"\nAttempting to commit {len(leads)} leads to the database...")
    
    # Use explicit column names and ensure price is cast to integer
    insert_query = text("""
        INSERT INTO leads_sandbox 
        (address, lead_rating, price, beds, baths, sqft, property_type, last_source_url, last_notes)
        VALUES (:address, :rating, :price, :beds, :baths, :sqft, :property_type, :url, :notes)
    """)
    
    with engine.begin() as conn:
        for lead in leads:
            # Clean data before insertion
            clean_data = {
                "address": lead.get("address"),
                "rating": lead.get("rating", "C"),
                "price": int(lead["price"]) if lead.get("price") else None,
                "beds": float(lead["beds"]) if lead.get("beds") else None,
                "baths": float(lead["baths"]) if lead.get("baths") else None,
                "sqft": float(lead["sqft"]) if lead.get("sqft") else None,
                "property_type": lead.get("property_type", "Unknown"),
                "url": lead.get("url"),
                "notes": f"v3.0.0 Regex: Price={lead.get('price')}"
            }
            conn.execute(insert_query, clean_data)
            
    print("Database commit successful!")

if __name__ == "__main__":
    leads = asyncio.run(scrape_properties())
    save_to_sandbox(leads)