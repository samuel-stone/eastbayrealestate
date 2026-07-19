import os
import asyncio
import random
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
    
    # Wrap the async_playwright instance in Stealth
    async with Stealth().use_async(async_playwright()) as p:
        browser = await p.chromium.launch(headless=True)
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
                    # Patient human-like delay on the list page
                    await page.wait_for_timeout(random.randint(4000, 7000))
                except Exception as e:
                    print(f"Failed to load {list_url}: {e}")
                    break
                
                if page_num > 1 and "/page-" not in page.url:
                    break
                
                # 1. Extract all individual property links from the search page
                property_links = await page.locator("a[href^='/CA/']").evaluate_all(
                    "elements => elements.map(e => e.href)"
                )
                
                property_links = list(set(property_links))
                
                if not property_links:
                    print(f"No more listings found in {zip_code}.")
                    break
                    
                print(f"Discovered {len(property_links)} detail links. Processing slowly...")
                
                # 2. Iterate through each individual home detail page
                for url in property_links:
                    try:
                        print(f"-> Inspecting: {url}")
                        await page.goto(url, wait_until="domcontentloaded")
                        
                        # Extra long random delay to mimic reading the page and avoid IP bans
                        await page.wait_for_timeout(random.randint(5000, 9500)) 
                        
                        # Dynamic extraction
                        try:
                            await page.wait_for_selector('[data-rf-test-id="abp-price"]', timeout=10000)
                            raw_price = await page.locator('[data-rf-test-id="abp-price"]').first.inner_text()
                            price = int(raw_price.replace('$', '').replace(',', ''))
                        except:
                            price = None

                        try:
                            raw_beds = await page.locator('[data-rf-test-id="abp-beds"] > .statsValue').first.inner_text()
                            beds = float(raw_beds)
                        except:
                            beds = None

                        try:
                            raw_baths = await page.locator('[data-rf-test-id="abp-baths"] > .statsValue').first.inner_text()
                            baths = float(raw_baths)
                        except:
                            baths = None

                        try:
                            raw_sqft = await page.locator('[data-rf-test-id="abp-sqFt"] > .statsValue').first.inner_text()
                            sqft = float(raw_sqft.replace(',', ''))
                        except:
                            sqft = None

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
                # Standard delay before moving to the next pagination list
                await page.wait_for_timeout(random.randint(3000, 6000))

        await browser.close()
        return all_extracted_leads

def save_to_sandbox(leads):
    if not leads:
        print("No leads to save.")
        return
        
    print(f"\nSaving {len(leads)} detailed leads to the database...")
    
    insert_query = text("""
        INSERT INTO leads_sandbox 
        (address, lead_rating, price, beds, baths, sqft, property_type, last_source_url, last_notes)
        VALUES (:address, :rating, :price, :beds, :baths, :sqft, :property_type, :url, :notes)
    """)
    
    with engine.begin() as conn:
        for lead in leads:
            conn.execute(insert_query, {
                "address": lead["address"],
                "rating": lead["rating"],
                "price": lead["price"],
                "beds": lead["beds"],
                "baths": lead["baths"],
                "sqft": lead["sqft"],
                "property_type": lead["property_type"],
                "url": lead["url"],
                "notes": "Deep Stealth Crawler"
            })
            
    print("Database commit successful!")

if __name__ == "__main__":
    leads = asyncio.run(scrape_properties())
    save_to_sandbox(leads)