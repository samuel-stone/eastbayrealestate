import os
import time
import json
import requests
import pandas as pd
from google import genai
from dotenv import load_dotenv

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_HOST", "http://localhost:11434/api/generate")
MODEL_NAME = os.getenv("OLLAMA_MODEL", "llama3")
GEMINI_MODEL = "get-gemini-2.0-flash" if False else "gemini-2.0-flash"

def query_local_ollama(prompt):
    """Attempt free local inference via Ollama."""
    try:
        payload = {
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False
        }
        response = requests.post(OLLAMA_URL, json=payload, timeout=3)
        if response.status_code == 200:
            text = response.json().get("response", "").strip()
            if text:
                return text, "Local (Ollama / Llama3)"
    except Exception:
        pass
    return None, None

def query_cloud_gemini(prompt):
    """Escalate to Gemini API if local LLM is offline."""
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        return None, None
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
        if response and response.text:
            return response.text.strip(), "Cloud (Gemini API)"
    except Exception as e:
        print(f"[-] Gemini API escalation error: {e}")
    return None, None

def intelligent_reasoning(prompt):
    # Tier 1: Local Ollama
    result, source = query_local_ollama(prompt)
    if result:
        return result, source
    
    print("[!] Local Ollama offline. Escalating to Cloud Gemini API...")
    
    # Tier 2: Cloud Gemini API
    result, source = query_cloud_gemini(prompt)
    if result:
        return result, source
    
    print("[!] Cloud Gemini unavailable. Using deterministic fallback rule set.")
    # Tier 3: Deterministic Fallback
    fallback = (
        "- Analysis: High permit momentum and capital investment detected.\n"
        "- Strategy: Proactive pre-listing equity advisory and direct mail drop.\n"
        "- Next Action: Generate Avery mailing label and schedule door-drop."
    )
    return fallback, "Deterministic Fallback"

def run_autonomous_cycle():
    print("\n[🤖] Autonomous Agent Cycle Initiated (Hybrid Escalation Enabled)...")
    
    target_csv = "scored_rossmoor_targets.csv"
    if not os.path.exists(target_csv):
        target_csv = "moms_priority_local_leads.csv"
    
    if not os.path.exists(target_csv):
        print("[-] No target dataset found. Run discovery/scraping first.")
        return

    df = pd.read_csv(target_csv)
    top_leads = df.head(3)
    print(f"[+] Agent selected {len(top_leads)} high-priority properties for autonomous evaluation.")

    agent_actions = []
    for idx, row in top_leads.iterrows():
        address = row.get('address')
        city = row.get('city', 'Walnut Creek')
        permits = row.get('building_permit_count_24m', 0)
        project_type = row.get('major_project_type', 'General Renovation')

        prompt = (
            f"You are an expert real estate prospecting agent. Evaluate property at {address}, {city}. "
            f"It has {permits} building permits in 24 months for '{project_type}'. "
            "Provide 3 precise bullet points for a direct mail and door-drop campaign."
        )

        print(f"[*] Evaluating {address}...")
        strategy, source = intelligent_reasoning(prompt)
        print(f"    ↳ Handled by: {source}")
        
        agent_actions.append({
            "address": address,
            "city": city,
            "permits": permits,
            "agent_strategy": strategy,
            "ai_source": source,
            "timestamp": pd.Timestamp.now().isoformat()
        })
        time.sleep(1)

    audit_df = pd.DataFrame(agent_actions)
    audit_file = "agent_autonomous_audit.csv"
    audit_df.to_csv(audit_file, index=False)
    print(f"[+] Agent successfully committed decisions to '{audit_file}'.")

    os.system("python3 generate_avery_labels.py")
    print("[+] Agent successfully generated updated Avery direct-mail mailing labels.")
    print("[✓] Autonomous cycle completed successfully.\n")

if __name__ == "__main__":
    run_autonomous_cycle()
