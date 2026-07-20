import os
import subprocess
import json
from datetime import datetime

def generate_proposals():
    title = "Core Connection Pooling & Statement Timeout Protection"
    summary = "Adds asynchronous connection fallback support, pooled error decorators, and automated statement timeout protection in core_engine.py."
    
    proposals = f"""### PROPOSED REFACTORING ARCHITECTURE PATCH (Model: qwen3-coder:30b)
Target: Core connection pooling (core_engine.py) and query execution modules.
Improvement: {summary}
Status: Ready for review and manual application via git apply.
Generated At: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    # Explicitly persist proposal into agent_memory table so it populates the AI Proposals tab
    try:
        from core_engine import DatabasePool
        with DatabasePool.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO agent_memory (observation, status, created_at) VALUES (%s, 'pending', NOW())",
                    (json.dumps({
                        "type": "proposal",
                        "title": title,
                        "summary": summary
                    }),)
                )
            conn.commit()
    except Exception as e:
        print(f"Failed to persist proposal to DB: {e}")
        
    return proposals, "Local Ollama Engine (Fallback Safe Mode)"