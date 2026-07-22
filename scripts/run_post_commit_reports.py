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
