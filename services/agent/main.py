import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from automation_engine.agent_tools import (
    failed_jobs, 
    retry_failed_jobs, 
    send_email_notification, 
    document_run_summary,
    recent_jobs,
    draft_enrichment_plan,
    generate_scraper_script
)

load_dotenv()

def run_safe_mode_repair() -> str:
    """Deterministic fallback: Repairs jobs without calling any AI."""
    print("--- SAFE MODE: Executing Deterministic Repair ---")
    jobs = failed_jobs()
    if jobs:
        msg = retry_failed_jobs()
        try:
            send_email_notification("Alert: System Repair Executed (Safe Mode)", f"Repaired {len(jobs)} jobs.")
        except Exception:
            pass
        return f"Safe Mode Repair: {msg}"
    return "Safe Mode: No jobs to repair."

def analyze_system() -> str:
    """Entry point for the service with AI-powered tool execution."""
    try:
        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        tools = [failed_jobs, retry_failed_jobs, send_email_notification, document_run_summary]
        config = types.GenerateContentConfig(tools=tools, temperature=0.0)
        
        # Using the current stable production model
        chat = client.chats.create(model='gemini-3.5-flash', config=config)
        
        prompt = """
        You are the Senior Autonomous Growth Analyst.
        1. Call 'failed_jobs' to check for errors.
        2. If jobs are failed, call 'retry_failed_jobs' and 'send_email_notification'.
        3. If no jobs are failed, call 'document_run_summary'.
        """
        
        response = chat.send_message(prompt)
        return response.text
        
    except Exception as e:
        print(f"--- AI SERVICE UNAVAILABLE: {str(e)} ---")
        return run_safe_mode_repair()

if __name__ == "__main__":
    print(analyze_system())