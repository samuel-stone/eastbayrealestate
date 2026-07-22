import os
import time
import random
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted
import requests
import json

# Configure Gemini
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

def route_task(task_type: str) -> str:
    """
    Hybrid commit routing.
    Simple/cheap checks go to local Ollama; judgment calls go to Gemini.
    """
    if task_type in ["formatting", "lint_summary", "static_analysis_restatement"]:
        return "ollama"
    return "gemini"

def ask_ai(prompt: str, task_type: str = "judgment_call", max_retries: int = 4):
    """
    Routes the prompt to the selected model provider based on the routing rule.
    Includes Exponential Backoff for handling Gemini API rate limits (HTTP 429).
    """
    provider = route_task(task_type)
    print(f"🧠 Routing task '{task_type}' to provider: {provider}")
    
    if provider == "gemini":
        # Using Flash for a higher free tier RPM limit
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Exponential backoff loop
        for attempt in range(max_retries):
            try:
                response = model.generate_content(prompt)
                clean_text = response.text.replace("```json", "").replace("```", "").strip()
                return clean_text
                
            except ResourceExhausted as e:
                if attempt == max_retries - 1:
                    print(f"❌ Gemini rate limit exceeded after {max_retries} retries.")
                    raise e
                    
                # Calculate backoff time: 2^attempt + random jitter
                sleep_time = (2 ** attempt) + random.uniform(0, 1)
                print(f"⚠️ Rate limit hit (429). Retrying in {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)
                
    elif provider == "ollama":
        url = "http://localhost:11434/api/generate"
        payload = {
            "model": "llama3.2:3b",
            "prompt": prompt,
            "stream": False
        }
        res = requests.post(url, json=payload)
        res.raise_for_status()
        return res.json().get("response", "")
        
    else:
        raise ValueError(f"Unknown provider: {provider}")
