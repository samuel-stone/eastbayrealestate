import os
import json
import subprocess
from datetime import datetime

def generate_proposals():
    """Generates codebase refactoring and ML architecture proposals using local Ollama with robust error handling."""
    model = os.environ.get("OLLAMA_MODEL", "qwen3-coder:30b")
    
    # Try calling local ollama model directly
    try:
        res = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=5)
        if res.returncode == 0:
            prompt = (
                "Analyze the East Bay Real Estate codebase connection pooling and lead scoring modules. "
                "Provide a precise architectural refactoring proposal or ML enhancement."
            )
            ollama_res = subprocess.run(
                ["ollama", "run", model, prompt], 
                capture_output=True, text=True, timeout=45
            )
            if ollama_res.returncode == 0 and ollama_res.stdout.strip():
                proposal_text = ollama_res.stdout.strip()
                
                # Persist into database agent_memory
                from core_engine import DatabasePool
                with DatabasePool.get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            "INSERT INTO agent_memory (observation, status, created_at) VALUES (%s, 'pending', NOW())",
                            (json.dumps({
                                "type": "proposal",
                                "title": f"AI Architectural Proposal ({model})",
                                "summary": proposal_text[:300] + "..."
                            }),)
                        )
                    conn.commit()
                return proposal_text, f"Local Ollama ({model})"
    except Exception as e:
        print(f"Ollama local execution caught exception: {e}")

    # Fallback only if local engine is completely unreachable
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    fallback_title = "Core Connection Pooling & Statement Timeout Protection"
    fallback_summary = "Adds asynchronous connection fallback support, pooled error decorators, and automated statement timeout protection."
    
    from core_engine import DatabasePool
    try:
        with DatabasePool.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO agent_memory (observation, status, created_at) VALUES (%s, 'pending', NOW())",
                    (json.dumps({
                        "type": "proposal",
                        "title": fallback_title,
                        "summary": fallback_summary
                    }),)
                )
            conn.commit()
    except Exception as db_err:
        print(f"DB fallback insert error: {db_err}")

    fallback_proposal = f"""### PROPOSED REFACTORING ARCHITECTURE PATCH (Model: {model} [Offline Fallback Mode])
- Target: Core connection pooling (`core_engine.py`) and query execution modules.
- Improvement: {fallback_summary}
- Status: Ready for review and manual application.
- Generated At: {timestamp}
"""
    return fallback_proposal, f"Safe Fallback Engine ({model})"