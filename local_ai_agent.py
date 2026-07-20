import os
import requests
import json
import pandas as pd

OLLAMA_URL = os.getenv("OLLAMA_HOST", "http://localhost:11434/api/generate")
MODEL_NAME = os.getenv("OLLAMA_MODEL", "llama3")

def generate_local_strategy(prompt):
    try:
        payload = {
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False
        }
        response = requests.post(OLLAMA_URL, json=payload, timeout=30)
        if response.status_code == 200:
            return response.json().get("response", "No response generated.")
        else:
            return f"Error: Local LLM returned status {response.status_code}"
    except Exception as e:
        return f"Local LLM connection error: {e}. Make sure Ollama is running (ollama serve)."

def run_local_pipeline():
    csv_file = "scored_rossmoor_targets.csv"
    if not os.path.exists(csv_file):
        csv_file = "moms_priority_local_leads.csv"
    
    if not os.path.exists(csv_file):
        print("[-] No lead dataset found for local AI analysis.")
        return

    df = pd.read_csv(csv_file)
    strategies = []
    
    print(f"[+] Running local AI analysis using model '{MODEL_NAME}' across {len(df)} properties...")
    for idx, row in df.iterrows():
        prompt = f"Analyze real estate property lead at {row.get('address')} with {row.get('building_permit_count_24m', 0)} building permits ({row.get('major_project_type', 'General')}). Provide 3 concise strategic outreach bullet points for a real estate agent."
        print(f"[*] Processing: {row.get('address')}...")
        strat = generate_local_strategy(prompt)
        strategies.append(strat)

    df['local_ai_strategy'] = strategies
    output_file = "local_ai_analyzed_leads.csv"
    df.to_csv(output_file, index=False)
    print(f"[+] Successfully saved local AI insights to '{output_file}!'")

if __name__ == "__main__":
    run_local_pipeline()
