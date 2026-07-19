import os
import time
import json
import shutil
from datetime import datetime
from pathlib import Path
import psycopg2
from dotenv import load_dotenv
from google import genai

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

def get_db_connection(): return psycopg2.connect(DATABASE_URL)

def scan_logs_for_errors():
    Path("errors").mkdir(exist_ok=True)
    found_errors = []
    for log_file in Path(".").rglob("*.log"):
        try:
            content = log_file.read_text()
            if "error" in content.lower() or "failed" in content.lower():
                found_errors.append(str(log_file))
        except: continue
    return found_errors

def get_resource_report():
    total, used, free = shutil.disk_usage(".")
    db_size = "Unknown"
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT pg_size_pretty(pg_database_size(current_database()));")
        db_size = cur.fetchone()[0]
        cur.close(); conn.close()
    except: pass
    return {"disk_free_gb": round(free / (2**30), 2), "db_size": db_size}

def gather_business_intelligence():
    """Analyzes the actual lead database and market intake."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # 1. Analyze Prospect Quality (High-value targets)
        cur.execute("SELECT lead_rating, COUNT(*) FROM leads GROUP BY lead_rating;")
        lead_ratings = cur.fetchall()
        
        # 2. Market Intake (Scraped data volume)
        cur.execute("SELECT COUNT(*) FROM scraped_property_data WHERE created_at > NOW() - INTERVAL '24 hours';")
        scraped_volume = cur.fetchone()[0]
        
        cur.close(); conn.close()
        return {"lead_ratings": lead_ratings, "scraped_volume_24h": scraped_volume}
    except Exception as e:
        return {"error": str(e)}

def perform_local_research():
    # Gather the data
    data = {
        "timestamp": datetime.now().isoformat(),
        "business_intel": gather_business_intelligence()
    }
    
    # Bypass filesystem: Print directly to logs so Railway catches it
    print(f"--- AGENT RESEARCH DATA ---")
    print(json.dumps(data, indent=2))
    print(f"---------------------------")
    
    return data

def autonomous_evolution_cycle(payload):
    research = perform_local_research()
    data = json.loads(payload)
    focus = data.get("focus", "general engineering")
    
    if not client:
        print(f"LLM offline. Research cached.")
        return

    prompt = f"""
    You are the Growth Architect for your Real Estate platform. Focus: {focus}.
    
    BUSINESS INTELLIGENCE: {json.dumps(research['business_intel'])}
    SYSTEM VITALS: {json.dumps(research['tech_vitals'])}
    
    1. BUSINESS STRATEGY: You have {research['business_intel'].get('scraped_volume_24h', 0)} new property scrapes. 
       Look at the 'lead_ratings' breakdown. Suggest how to prioritize the high-rated leads vs. the new scraped data.
    2. TECHNICAL ACTION: Propose landing page, SEO, or lead-capture code changes to turn scraped properties into leads.
    3. COMMIT PROPOSALS: Provide specific code change blocks.
    
    Return markdown only.
    """
    
    response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
    
    Path("planning").mkdir(exist_ok=True)
    filename = f"planning/plan_{focus}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(filename, "w") as f: f.write(response.text)
    print(f"Plan created: {filename}")

def process_task_queue():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, task_type, payload FROM ai_tasks WHERE status='pending' ORDER BY priority DESC, created_at ASC LIMIT 1;")
        task = cur.fetchone()
        if not task: cur.close(); conn.close(); return
        
        task_id, task_type, payload = task
        
        # FIX: Ensure payload is a dictionary
        if isinstance(payload, str):
            data = json.loads(payload)
        else:
            data = payload
            
        if task_type in ["autonomous_audit", "research_only"]:
            autonomous_evolution_cycle(json.dumps(data)) # Ensure it's passed as string
            
        cur.execute("UPDATE ai_tasks SET status='completed' WHERE id=%s;", (task_id,))
        conn.commit(); cur.close(); conn.close()
    except Exception as e: 
        print(f"Process error: {e}")

def main():
    print("Agent module loaded. Fallback mode active.")
    while True:
        process_task_queue()
        time.sleep(3600)

if __name__ == "__main__": main()