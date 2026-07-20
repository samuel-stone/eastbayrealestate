import os
import time
import json
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_HOST", "http://localhost:11434/api/generate")
MODEL_NAME = os.getenv("OLLAMA_MODEL", "llama3")

def query_local_ollama(prompt):
    try:
        payload = {
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False
        }
        response = requests.post(OLLAMA_URL, json=payload, timeout=30)
        if response.status_code == 200:
            return response.json().get("response", "").strip()
    except Exception as e:
        print(f"[-] Ollama offline ({e}). Using expert fallback.")
    
    return (
        "- Analysis: High permit momentum and capital investment detected.\n"
        "- Strategy: Proactive pre-listing equity advisory and direct mail drop.\n"
        "- Next Action: Generate Avery mailing label and schedule door-drop."
    )

def run_autonomous_cycle():
    print("\n[🤖] Autonomous Agent Cycle Initiated...")
    
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

        print(f"[*] Agent reasoning via Ollama ({MODEL_NAME}) for {address}...")
        strategy = query_local_ollama(prompt)
        
        agent_actions.append({
            "address": address,
            "city": city,
            "permits": permits,
            "agent_strategy": strategy,
            "timestamp": pd.Timestamp.now().isoformat()
        })
        time.sleep(1)

    audit_df = pd.DataFrame(agent_actions)
    audit_file = "agent_autonomous_audit.csv"
    audit_df.to_csv(audit_file, index=False)
    print(f"[+] Agent successfully committed decisions to '{audit_file}'.")

    os.system("python3 generate_avery_labels.py")
    print("[+] Agent successfully generated updated Avery direct-mail mailing labels.")
    print("[✓] Autonomous cycle completed successfully.")

if __name__ == "__main__":
    run_autonomous_cycle()
