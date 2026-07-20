import os
import requests
import json
from google import genai
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_HOST", "http://localhost:11434/api/generate")
MODEL_NAME = os.getenv("OLLAMA_MODEL", "llama3")
GEMINI_MODEL = "gemini-2.0-flash"

def get_db_engine():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL not set!")
    return create_engine(db_url.replace("postgres://", "postgresql://", 1))

def generate_strategy(prompt):
    try:
        payload = {"model": MODEL_NAME, "prompt": prompt, "stream": False}
        response = requests.post(OLLAMA_URL, json=payload, timeout=4)
        if response.status_code == 200:
            text_resp = response.json().get("response")
            if text_resp:
                return text_resp, "Local (Ollama / Llama3)"
    except Exception:
        pass

    api_key = os.getenv('GEMINI_API_KEY')
    if api_key:
        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
            if response and response.text:
                return response.text, "Cloud (Gemini API)"
        except Exception:
            pass

    return "- Focus: High permit momentum.\n- Angle: Pre-listing equity advisory.\n- Action: Add to door-drop route.", "Deterministic Fallback"

def run_task():
    print("[+] Starting Hybrid AI Enrichment Task...")
    engine = get_db_engine()
    
    with engine.begin() as conn:
        leads = conn.execute(text("""
            SELECT l.id, l.address, l.city, f.building_permit_count_24m, f.major_project_type
            FROM leads l
            JOIN prospect_features f ON l.id = f.lead_id
            WHERE f.building_permit_count_24m >= 2
            LIMIT 20;
        """)).fetchall()

        print(f"[+] Found {len(leads)} properties for hybrid AI enrichment.")
        for lead in leads:
            lead_id, address, city, permits, project_type = lead
            prompt = f"Analyze real estate property lead at {address} in {city} with {permits} building permits ({project_type or 'General'}). Provide 3 concise strategic outreach bullet points for a real estate agent."
            
            strategy, source = generate_strategy(prompt)
            print(f"[*] Enriched {address} via {source}")

            conn.execute(text("""
                INSERT INTO agent_memory (key, value, created_at, updated_at)
                VALUES (:key, :value, NOW(), NOW())
                ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = NOW();
            """), {"key": f"lead_strategy_{lead_id}", "value": json.dumps({"address": address, "strategy": strategy, "source": source})})

    print("[+] Hybrid AI Enrichment Task completed successfully!")

if __name__ == "__main__":
    run_task()
