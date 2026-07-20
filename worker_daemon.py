import time
import logging
import json
from db_pool import get_pooled_connection

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def process_task_queue():
    logging.info("[+] Production Worker Daemon online. Polling ai_tasks queue...")
    backoff = 1
    while True:
        try:
            with get_pooled_connection() as conn:
                with conn.cursor() as cur:
                    # Fetch queued task
                    cur.execute("""
                        SELECT id, task_type, payload 
                        FROM ai_tasks 
                        WHERE status = 'queued' 
                        ORDER BY priority DESC, created_at ASC 
                        LIMIT 1 FOR UPDATE SKIP LOCKED;
                    """)
                    task = cur.fetchone()
                    
                    if task:
                        task_id, task_type, payload = task
                        logging.info(f"[*] Executing task ID {task_id}: {task_type}")
                        
                        # Mark as running
                        cur.execute("UPDATE ai_tasks SET status = 'running' WHERE id = %s;", (task_id,))
                        conn.commit()
                        
                        # Simulate task execution / hook into registry
                        time.sleep(1)
                        
                        # Mark as completed
                        cur.execute("UPDATE ai_tasks SET status = 'completed' WHERE id = %s;", (task_id,))
                        conn.commit()
                        logging.info(f"[+] Task ID {task_id} completed successfully.")
                        backoff = 1  # Reset backoff on success
                    else:
                        time.sleep(3) # Sleep if queue is empty
        except Exception as e:
            logging.error(f"[-] Worker execution error: {e}. Backing off for {backoff}s...")
            time.sleep(backoff)
            backoff = min(backoff * 2, 60)  # Exponential backoff capped at 60s

if __name__ == "__main__":
    process_task_queue()
