import os
import json
import urllib.request
import urllib.error
from datetime import datetime
from core_engine import DatabasePool

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

def load_repository_context():
    """
    Load real repository files so the AI reviews actual code
    instead of generating generic architecture advice.
    """
    files_to_review = [
        "app.py",
        "core_engine.py",
        "automation_engine/database.py",
        "automation_engine/worker.py",
        "automation_engine/task_registry.py",
        "automation_engine/ai_client.py",
    ]
    
    context_blocks = []
    print("[AI Architect] Loading repository context...")
    for filename in files_to_review:
        path = os.path.join(ROOT_DIR, filename)
        if not os.path.exists(path):
            print(f"[AI Architect] Skipping missing file: {filename}")
            continue
        try:
            with open(path, "r", encoding="utf-8") as file:
                content = file.read()
            # Prevent oversized Ollama prompts
            content = content[:10000]
            context_blocks.append(f"""
FILE: {filename}
==================================================
{content}
""")
        except Exception as e:
            print(f"[AI Architect] Failed reading {filename}: {e}")
            
    if not context_blocks:
        return "No repository files were available for review."
        
    return "\n".join(context_blocks)


def build_architect_prompt():
    repository_context = load_repository_context()
    return f"""
You are the senior Codebase Architect for the East Bay Real Estate automation platform. 

Your job is to review the REAL PROVIDED CODE ONLY. Do not make generic architectural assumptions or suggest adding features that already exist in the source files.

Repository stack & existing modules:
- Python, Streamlit, PostgreSQL, psycopg2, custom DatabasePool (`core_engine.py`)
- Background worker & execution event telemetry (`automation_engine/worker.py`, `execution_logger.py`)
- Hybrid AI router (`automation_engine/ai_client.py`)

==================================================
STRICT GROUNDING & EVIDENCE RULES (12 COMMANDMENTS)
==================================================
1. NEVER invent missing features, libraries, or frameworks (e.g., do not recommend SQLAlchemy, Flask, or Celery).
2. NEVER claim logging or monitoring is missing; `execution_events` and `database.py` handle live telemetry logging.
3. NEVER assume database schema structures outside of what is explicitly defined in the provided code snippets.
4. Every single finding or recommendation MUST cite direct evidence from the supplied files, including the filename and exact logic section.
5. If a security or performance concern cannot be proven via the provided code lines, you must state: "Insufficient evidence."
6. Do not provide generic textbook definitions or high-level summaries of software engineering principles.
7. Focus exclusively on concrete code constructs (e.g., connection pool acquisition limits, exception rollbacks, query performance).
8. Verify that database transactions utilize proper context managers or explicit commit/rollback blocks.
9. Check that asynchronous or blocking calls in worker daemons handle timeouts cleanly without hanging threads.
10. Ensure JSONB database fields are queried using proper operators (`->>`, `->`) rather than raw string matching.
11. Validate that environment variables (like `DATABASE_URL` or `GEMINI_API_KEY`) include safe fallback or error handling.
12. If no flaws are found in a reviewed module, explicitly state that the module meets current production baseline standards.

For every actionable finding include:
- Finding Title
- Exact File Evidence (filename and code snippet)
- Risk / Impact Analysis
- Actionable Recommendation
- Confidence Score (0-100)

Return a structured engineering review based solely on the code below:

{repository_context}
"""


def call_ollama(prompt, target_model):
    print(f"\n[AI Architect] Pinging local Ollama API at http://127.0.0.1:11434/api/generate for model '{target_model}' (Timeout: 120s)...")
    url = "http://127.0.0.1:11434/api/generate"
    proposal_text = ""
    
    try:
        payload = json.dumps({
            "model": target_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.05,
                "num_predict": 1500
            }
        }).encode("utf-8")
        
        request = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        
        with urllib.request.urlopen(request, timeout=120) as response:
            if response.status != 200:
                raise RuntimeError(f"Ollama returned HTTP {response.status}")
            data = json.loads(response.read().decode("utf-8"))
            proposal_text = data.get("response", "").strip()
            
    except Exception as e:
        print(f"[AI Architect] Ollama generation error: {type(e).__name__} {e}")
        
    return proposal_text


def fallback_proposal():
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return f"""
### ACTIONABLE REFACTORING PROPOSAL
Generated by Safe Grounded Fallback Engine

Timestamp: {timestamp}

Finding:
Connection pool boundary and transaction safety check.

Evidence:
`core_engine.py` - DatabasePool connection lifecycle.

Risk:
Potential unreturned connections during high concurrency worker tasks.

Recommendation:
1. Ensure `DatabasePool.get_connection()` context manager strictly guarantees `putconn` execution in `finally` blocks.
2. Verify JSONB query operators across analytical views.

Verification:
- Run database connection pool load tests.
- Review worker execution logs.
"""


def save_to_agent_memory(proposal_text, source_engine):
    timestamp_slug = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    title_str = f"Actionable Architecture Patch {timestamp_slug}"
    
    observation = {
        "type": "proposal",
        "title": title_str,
        "source_agent": "code_architect",
        "source_engine": source_engine,
        "summary": proposal_text[:350] + "...",
        "full_proposal": proposal_text,
        "created_at": timestamp_slug
    }
    
    try:
        with DatabasePool.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO agent_memory (observation, status, created_at)
                    VALUES (%s, 'pending', NOW())
                """, (json.dumps(observation, ensure_ascii=False),))
            conn.commit()
        print(f"[AI Architect] Successfully persisted proposal '{title_str}' to database agent_memory.")
    except Exception as db_err:
        print(f"[AI Architect] Failed to persist proposal to agent memory: {db_err}")


def generate_proposals():
    target_model = os.environ.get("OLLAMA_MODEL", "llama3.2:3b")
    proposal_text = ""
    source_engine = ""
    
    try:
        prompt = build_architect_prompt()
        proposal_text = call_ollama(prompt, target_model)
        if proposal_text:
            source_engine = f"Local Ollama API ({target_model})"
            print(f"[AI Architect] Generated {len(proposal_text)} chars")
    except Exception as e:
        print(f"[AI Architect] Ollama failed: {e}")
        
    if not proposal_text:
        proposal_text = fallback_proposal()
        source_engine = f"Safe Fallback Engine ({target_model})"
        
    save_to_agent_memory(proposal_text, source_engine)
    return proposal_text, source_engine