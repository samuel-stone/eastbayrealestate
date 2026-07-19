import os
from datetime import datetime
from automation_engine.database import get_connection, add_job
from automation_engine.notifier import notify

def failed_jobs():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT name, attempts, last_error
        FROM jobs
        WHERE status='failed'
        ORDER BY created_at DESC
        LIMIT 10
    """)

    rows = cur.fetchall()

    conn.close()

    return rows


def recent_jobs():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT name,status,created_at
        FROM jobs
        ORDER BY created_at DESC
        LIMIT 10
    """)

    rows = cur.fetchall()

    conn.close()

    return rows


def schedule_engine_task(task_name):
    """
    Allows the agent to schedule an asynchronous task or report.
    Valid task names: 'scrape_listings', 'scrape_danville', 'process_leads', 'daily_market_report'.
    """
    valid_tasks = ["scrape_listings", "scrape_danville", "process_leads", "daily_market_report"]
    
    if task_name not in valid_tasks:
        return f"Error: '{task_name}' is not a recognized task."
        
    try:
        add_job(task_name)
        
        if task_name == "daily_market_report":
            notify("Agent triggered a daily market report run.")
            
        return f"Success: Task '{task_name}' has been queued for execution."
    except Exception as e:
        return f"Failed to queue task '{task_name}': {str(e)}"


def document_run_summary(title, details):
    """
    Writes a timestamped markdown record of agent actions to the documentation folder.
    """
    os.makedirs("docs", exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    filepath = f"docs/agent_summary_{date_str}.md"
    
    time_str = datetime.now().strftime("%H:%M:%S")
    
    with open(filepath, "a") as doc:
        doc.write(f"### {time_str} - {title}\n")
        doc.write(f"{details}\n\n")
        
    return f"Documentation successfully appended to {filepath}"


def draft_enrichment_plan(target_source, context_notes=""):
    """
    Allows the agent to document and outline a strategy for a new data source or scraper bypass.
    """
    os.makedirs("planning", exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    filepath = f"planning/enrichment_strategy_{target_source.lower()}_{date_str}.md"
    
    with open(filepath, "w") as doc:
        doc.write(f"# Data Enrichment Strategy: {target_source}\n")
        doc.write(f"**Date Generated:** {date_str}\n\n")
        doc.write(f"## Objective\n{context_notes}\n\n")
        doc.write("## Proposed Bypass & Integration Architecture\n")
        doc.write("### 1. Identity Masking\n")
        doc.write("- Implement residential proxy rotation (e.g., BrightData, Smartproxy) to distribute requests and avoid IP bans.\n")
        doc.write("- Use `undetected-chromedriver` or `Playwright` to simulate human interaction, ensuring proper TLS fingerprinting.\n\n")
        doc.write("### 2. Data Extraction\n")
        doc.write("- Avoid parsing DOM HTML where possible. Instead, intercept the internal XHR/Fetch API JSON payloads using browser network tools.\n")
        doc.write("- Introduce randomized delays (`time.sleep` between 3-9 seconds) and non-linear mouse movements.\n\n")
        doc.write("### 3. Alternative Fallbacks\n")
        doc.write("- If frontend scraping fails, evaluate secondary APIs like ATTOM Data or RentCast for backend data enrichment.\n")
        
    return f"Successfully drafted enrichment architecture for {target_source} in {filepath}"

def generate_scraper_script(target_source, script_content=None):
    """
    Allows the agent to write executable Python scraper code to the disk.
    """
    os.makedirs("scraper", exist_ok=True)
    filename = f"scraper/scrape_{target_source.lower()}.py"
    
    # If no dynamic content is provided by the LLM yet, use the architectural template
    if not script_content:
        script_content = f"""import time
from playwright.sync_api import sync_playwright

def run_scraper():
    print("Initializing headless browser bypass for {target_source}...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        # TODO: Implement stealth navigation and XHR interception here
        print("Navigating to target...")
        # page.goto("https://www.{target_source.lower().replace('_', '')}.com/rossmore-ca") 
        
        time.sleep(3) # Simulate human delay
        print("Data extraction payload intercepted.")
        
        browser.close()

if __name__ == "__main__":
    run_scraper()
"""
    
    with open(filename, "w") as code_file:
        code_file.write(script_content)
        
    return f"Executable scraper script generated successfully at {filename}"