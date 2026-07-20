import os
import requests
import json
from google import genai
from dotenv import load_dotenv

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_HOST", "http://localhost:11434/api/generate")
MODEL_NAME = os.getenv("OLLAMA_MODEL", "llama3")
GEMINI_MODEL = "gemini-2.0-flash"

def get_codebase_context():
    """Reads core project files to provide context for AI architectural review."""
    key_files = ['app.py', 'db_utils.py', 'local_autonomous_agent.py', 'scraper/scrape_redfin.py']
    context = ""
    for file in key_files:
        if os.path.exists(file):
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Include snippet or summary to keep token count optimal
                context += f"\n--- FILE: {file} ---\n{content[:2500]}\n"
    return context

def generate_proposals():
    code_context = get_codebase_context()
    prompt = (
        "You are an elite Senior Data Systems Architect. Review the following real estate data pipeline and Streamlit dashboard codebase:\n"
        f"{code_context}\n\n"
        "Provide:\n"
        "1. Three high-impact codebase improvements (performance, reliability, or cleanliness).\n"
        "2. Three innovative feature expansion proposals for real estate prospecting and agent workflow automation.\n"
        "Format with clear headings and actionable bullet points."
    )

    # 1. Try Local Ollama first
    try:
        payload = {"model": MODEL_NAME, "prompt": prompt, "stream": False}
        response = requests.post(OLLAMA_URL, json=payload, timeout=10)
        if response.status_code == 200:
            text = response.json().get("response")
            if text:
                return text, "Local (Ollama / Llama3)"
    except Exception:
        pass

    # 2. Escalate to Gemini API
    api_key = os.getenv('GEMINI_API_KEY')
    if api_key:
        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
            if response and response.text:
                return response.text.strip(), "Cloud (Gemini API)"
        except Exception:
            pass

    # 3. Fallback proposal
    return (
        "### 1. Codebase Improvements\n"
        "- Implement asynchronous database pooling for high-concurrency permit ingestion.\n"
        "- Add comprehensive unit tests using `pytest` for scraper HTML parsers.\n"
        "- Introduce structured JSON logging across all worker daemons.\n\n"
        "### 2. Feature Expansion Proposals\n"
        "- Automated SMS alerts via Twilio for top-tier whale property discoveries.\n"
        "- Interactive Folium/Mapbox spatial mapping tab in Streamlit for door-drop route optimization.\n"
        "- Predictive ML listing probability scoring based on 24-month permit velocity."
    ), "Deterministic Fallback"

if __name__ == "__main__":
    prop, source = generate_proposals()
    print(f"=== Codebase & Feature Proposals (Source: {source}) ===")
    print(prop)