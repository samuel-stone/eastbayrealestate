import os
import sys
import psycopg2
from datetime import datetime

# Add root directory to path so we can import internal modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code_architect import generate_proposals
from analytics_architect import generate_analytics_notebook

def log_to_agent_memory(title, summary):
    """Saves the auto-generated report directly into the live agent_memory table."""
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("[-] DATABASE_URL not found in environment.")
        return
        
    try:
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        observation = f'{{"type": "post_commit_report", "title": "{title}", "summary": "{summary}"}}'
        cur.execute(
            "INSERT INTO agent_memory (observation, created_at) VALUES (%s, %s)",
            (observation, datetime.now())
        )
        conn.commit()
        cur.close()
        conn.close()
        print(f"[+] Successfully logged '{title}' to database agent_memory!")
    except Exception as e:
        print(f"[-] Failed to write report to database: {e}")

if __name__ == "__main__":
    print("[+] Triggering automated post-commit reporting workflow...")
    
    # 1. Run Codebase Architect Review
    proposals, source = generate_proposals()
    log_to_agent_memory(f"Codebase Review ({source})", proposals[:500].replace('\n', ' '))
    
    # 2. Run Analytics Notebook Generator
    nb_file = generate_analytics_notebook()
    log_to_agent_memory("Analytics Notebook Compilation", f"Successfully generated notebook file: {nb_file}")
    
    print("[+] Automated post-commit pipeline completed successfully.")
