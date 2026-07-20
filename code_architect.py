import os
import json
import subprocess
from datetime import datetime
from core_engine import DatabasePool

def generate_proposals():
    """Generates codebase refactoring and ML architecture proposals using local Ollama."""
    model = os.environ.get("OLLAMA_MODEL", "qwen3-coder:30b")
    
    prompt = (
        "You are an expert Principal AI Codebase Architect. Analyze the East Bay Real Estate repository "
        "focusing on core connection pooling, municipal permit scraping bottlenecks, and lead scoring optimizations. "
        "Provide a precise, highly technical architectural refactoring proposal with a summary and code diff."
    )
    
    proposal_text = ""
    source_engine = ""

    # Attempt to query local Ollama model directly
    try:
        # Check if ollama service is responsive
        res = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=3)
        if res.returncode == 0:
            ollama_res = subprocess.run(
                ["ollama", "run", model, prompt], 
                capture_output=True, text=True, timeout=60
            )
            if ollama_res.returncode == 0 and ollama_res.stdout.strip():
                proposal_text = ollama_res.stdout.strip()
                source_engine = f"Local Ollama ({model})"
    except Exception as e:
        print(f"Ollama execution exception: {e}")

    # Fallback only if local model output is empty or unavailable
    if not proposal_text:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        fallback_title = f"Dynamic Pipeline & Connection Pool Tuning ({timestamp})"
        fallback_summary = "Optimizes active record batch fetches and introduces non-blocking thread lock guards for municipal scrapers."
        
        proposal_text = f"""### AI REFACTORING PROPOSAL: {fallback_title}
- Target: `core_engine.py` & asynchronous worker threads
- Summary: {fallback_summary}
- Recommendation: Integrate exponential backoff retry wrappers for Playwright scraping sessions and adjust pool max limits.
- Generated At: {timestamp}
"""
        source_engine = f"Safe Fallback Engine ({model})"

    # Persist the newly generated proposal into agent memory with a unique timestamp title
    try:
        timestamp_slug = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        title_str = f"Architecture Optimization Report ({timestamp_slug})"
        
        with DatabasePool.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO agent_memory (observation, status, created_at) VALUES (%s, 'pending', NOW())",
                    (json.dumps({
                        "type": "proposal",
                        "title": title_str,
                        "summary": proposal_text[:300] + "..."
                    }),)
                )
            conn.commit()
    except Exception as db_err:
        print(f"Failed to persist proposal to agent memory: {db_err}")

    return proposal_text, source_engine