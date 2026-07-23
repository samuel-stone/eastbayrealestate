import os
import sys
import subprocess

# Point Python to the root directory so it can find automation_engine
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from automation_engine.orchestrator import run_orchestration

def run():
    try:
        # Gather actual diff and sha
        diff = subprocess.check_output(["git", "diff", "HEAD~1", "HEAD"]).decode("utf-8")
        commit_sha = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("utf-8").strip()
    except subprocess.CalledProcessError:
        print("Could not retrieve git diff or sha. Ensure you are in a valid git repository.")
        return
    
    # Pass execution to the orchestrator
    run_orchestration(commit_sha, diff)

if __name__ == "__main__":
    run()
import os
import sys
import subprocess
import json

# Point Python to the root directory so it can find automation_engine
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from automation_engine.orchestrator import run_orchestration
from automation_engine.database import get_connection

def run():
    try:
        # Gather actual diff, sha, and commit stats
        diff = subprocess.check_output(["git", "diff", "HEAD~1", "HEAD"]).decode("utf-8")
        commit_sha = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("utf-8").strip()
        commit_stat = subprocess.check_output(["git", "diff", "--stat", "HEAD~1", "HEAD"]).decode("utf-8").strip()
    except subprocess.CalledProcessError:
        print("Could not retrieve git diff or sha. Ensure you are in a valid git repository.")
        return
    
    # Pass execution to the orchestrator
    run_orchestration(commit_sha, diff)
    
    # Print a rich terminal preview with added engineering intelligence
    print("\n" + "="*60)
    print(" 🤖 AUTONOMOUS AGENT POST-COMMIT REPORT & SYSTEM TELEMETRY ")
    print("="*60)
    print(f"Commit SHA: {commit_sha[:10]}")
    print("\n--- 1. Commit Impact (Git Stat) ---")
    print(commit_stat if commit_stat else "No file changes detected.")
    
    # Fetch DB telemetry (Queue backlog & pool metrics)
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # 1. Queue Backlog Stats
                cur.execute("""
                    SELECT status, COUNT(*) 
                    FROM jobs 
                    GROUP BY status;
                """)
                queue_rows = cur.fetchall()
                queue_summary = {r['status']: r['count'] for r in queue_rows} if queue_rows else {}

                # 2. Latest Agent Memory Entry
                cur.execute("""
                    SELECT observation, created_at 
                    FROM agent_memory 
                    ORDER BY created_at DESC 
                    LIMIT 1
                """)
                mem_row = cur.fetchone()
                
        print("\n--- 2. Background Worker Queue Backlog ---")
        if queue_summary:
            for status, count in queue_summary.items():
                print(f"  • {status.capitalize()}: {count} jobs")
        else:
            print("  • No active jobs in queue.")

        print("\n--- 3. Latest AI Review Summary ---")
        if mem_row:
            obs = mem_row['observation']
            if isinstance(obs, str):
                obs = json.loads(obs)
            print(f"Time: {mem_row['created_at']}")
            print(f"Source Agent: {obs.get('source_agent', 'single_reviewer')}")
            print(f"Summary:\n{obs.get('summary', str(obs))}")
        else:
            print("No memory records found.")
            
    except Exception as e:
        print(f"(Could not fetch database telemetry: {e})")
        
    print("="*60 + "\n")

if __name__ == "__main__":
    run()
    