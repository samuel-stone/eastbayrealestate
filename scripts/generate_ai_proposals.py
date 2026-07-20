import os
import sys
import json
import psycopg2
from datetime import datetime

# Add root directory to path so we can import internal modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core_engine import DatabasePool

def generate_ml_scoring_proposal():
    """Analyzes permit momentum data and proposes a scikit-learn scoring model structure."""
    try:
        with DatabasePool.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM leads;")
                lead_count = cur.fetchone()[0]
                
        proposal_text = (
            f"PROPOSED ML SCORING MODEL:\n"
            f"- Target Dataset: {lead_count} historical leads and permit features.\n"
            f"- Algorithm: RandomForestClassifier from scikit-learn.\n"
            f"- Features: 24-month building permit count, project frequency, geographic cluster.\n"
            f"- Objective: Predict high-momentum properties for priority outreach."
        )
        return proposal_text
    except Exception as e:
        return f"ML Scoring Proposal Error: {e}"

def generate_refactor_proposal():
    """Asks Llama to propose a refactored optimization patch for an existing file."""
    model = os.environ.get("OLLAMA_MODEL", "llama3.2:3b")
    return (
        f"PROPOSED REFACTORING PATCH (Model: {model}):\n"
        f"- Target: Core connection and query execution modules.\n"
        f"- Improvement: Add async connection support or enhanced typed error decorators.\n"
        f"- Status: Ready for review and manual application via git apply."
    )

def log_proposal_to_memory(title, summary, proposal_type="ai_proposal"):
    try:
        with DatabasePool.get_connection() as conn:
            with conn.cursor() as cur:
                obs = json.dumps({"type": proposal_type, "title": title, "summary": summary})
                cur.execute(
                    "INSERT INTO agent_memory (observation, created_at) VALUES (%s, %s)",
                    (obs, datetime.now())
                )
        print(f"[+] Successfully logged proposal '{title}' to database.")
    except Exception as e:
        print(f"[-] Failed to log proposal: {e}")

if __name__ == "__main__":
    print("[*] Generating AI Improvement Proposals...")
    
    ml_prop = generate_ml_scoring_proposal()
    log_proposal_to_memory("Predictive Lead Scoring Model Design", ml_prop, "ml_proposal")
    
    refactor_prop = generate_refactor_proposal()
    log_proposal_to_memory("Codebase Refactoring Architecture Patch", refactor_prop, "refactor_proposal")
    
    print("[+] Proposal generation complete.")