import os
import subprocess
from datetime import datetime
from core_engine import DatabasePool

def run_live_scraper(municipality):
    """Executes your existing live permit extraction pipeline for the specified municipality."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_output = f"[{timestamp}] Initializing live extraction worker for target: {municipality}...\n"
    
    # Point directly to your existing extractor script or module
    # Adjust this path if your extractor lives elsewhere (e.g., 'scripts/load_walnut_creek_permits.py')
    script_path = "scripts/load_walnut_creek_permits.py"
    
    if not os.path.exists(script_path):
        return log_output + f"[!] Error: Active scraper script not found at {script_path}. Please check your file path."

    try:
        log_output += f"[{timestamp}] Running existing extractor script: {script_path}...\n"
        res = subprocess.run(
            ["python3", script_path],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if res.stdout:
            log_output += res.stdout
        if res.stderr:
            log_output += res.stderr
            
        log_output += f"\n[{timestamp}] Extraction worker completed with exit code {res.returncode}."
        
        # Log successful run to agent memory
        try:
            with DatabasePool.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO agent_memory (observation, status, created_at) VALUES (%s, 'executed', NOW())",
                        (f'{{"type": "scraper", "title": "Live Scraper - {municipality}", "summary": "Successfully invoked existing permit extraction script."}}',)
                    )
                conn.commit()
        except Exception as db_err:
            log_output += f"\n[!] Note: Failed to log event to database: {db_err}"

    except subprocess.TimeoutExpired:
        log_output += f"\n[!] Extraction job timed out after 60 seconds."
    except Exception as e:
        log_output += f"\n[!] Extraction execution error: {e}"

    return log_output