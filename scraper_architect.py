import os
import subprocess
from datetime import datetime

def run_live_scraper(municipality="Walnut Creek"):
    """Actively triggers live extraction subprocesses or raises an explicit error if the script does not exist."""
    city_slug = municipality.lower().replace(" ", "_")
    
    # Determine which targeted scraper to execute
    if "zillow" in city_slug or "redfin" in city_slug:
        target_script = f"scripts/scrape_{city_slug}.py"
    else:
        target_script = "scripts/scrape_permits.py"
        
    if not os.path.exists(target_script):
        raise FileNotFoundError(
            f"Active scraper script for target '{municipality}' not found at `{target_script}`. "
            "Simulation has been disabled per configuration. Please provision the target scraper script."
        )
        
    log_output = f"[+] Initializing active extraction subprocess for {municipality} via `{target_script}`...\n"
    
    try:
        result = subprocess.run(
            ["python3", target_script, "--target", municipality], 
            capture_output=True, 
            text=True, 
            timeout=90
        )
        if result.returncode == 0:
            log_output += f"[+] Successfully completed active execution for {municipality}.\n"
            log_output += result.stdout if result.stdout else "[+] Records scraped successfully."
        else:
            raise RuntimeError(f"Scraper process exited with code {result.returncode}: {result.stderr}")
    except subprocess.TimeoutExpired:
        raise TimeoutError(f"Scraper execution for {municipality} timed out after 90 seconds.")
        
    # Log execution to database
    try:
        from core_engine import DatabasePool
        with DatabasePool.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO agent_memory (observation, created_at) VALUES (%s, NOW())",
                    (f'{{"type": "scraper", "title": "Portal Scrape - {municipality}", "summary": "Active extraction executed successfully"}}',)
                )
            conn.commit()
    except Exception:
        pass
        
    return log_output