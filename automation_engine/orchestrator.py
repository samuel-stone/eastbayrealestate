from automation_engine.memory_writer import write_to_memory
import json

def execute_review_job(commit_sha: str, diff_content: str):
    """
    Fallback review generator since code_reviewer was deprecated.
    You can wire this back up to your ai_client.py later!
    """
    return f"Automated AI Review Placeholder for {commit_sha} - Diff processed successfully."

def run_orchestration(commit_sha: str, diff_content: str):
    """
    Phase 2 Orchestrator: Currently wraps a single, grounded agent.
    Validates findings and writes to memory through the designated seam.
    """
    print(f"Orchestrating review for commit: {commit_sha}")
    
    # 1. Run the single grounded reviewer
    findings = execute_review_job(commit_sha, diff_content)
    
    if not findings:
        print("No valid findings produced.")
        return
        
    # 2. Format payload for memory seam
    payload = {
        "commit_sha": commit_sha,
        "diff": diff_content[:2000], # Truncate to prevent memory overflow 
        "summary": findings, 
        "source_agent": "single_reviewer"
    }
    
    # 3. Write via standard seam
    write_to_memory(payload)
    print("Orchestration complete. Written to memory.")