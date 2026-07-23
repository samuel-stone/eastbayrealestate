import time
import json
import logging
import signal
import sys
import traceback
from db_pool import get_pooled_connection
from scraper.scrape_redfin import run as run_scrape_listing

# Configure logging to match your existing setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

shutdown_flag = False

def handle_shutdown(signum, frame):
    """Catch Ctrl+C to shut down gracefully after the current task."""
    global shutdown_flag
    logging.info("[WORKER] Shutdown signal received.")
    shutdown_flag = True

# Register the signal handlers
signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)

def fetch_task():
    """Fetches the next pending task and locks it in the database."""
    with get_pooled_connection() as conn:
        with conn.cursor() as cur:
            # FOR UPDATE SKIP LOCKED prevents multiple workers from grabbing the same task
            cur.execute("""
                SELECT id, task_type, payload
                FROM ai_tasks
                WHERE status = 'pending'
                ORDER BY priority DESC, id ASC
                FOR UPDATE SKIP LOCKED
                LIMIT 1
            """)
            
            task = cur.fetchone()
            if not task:
                return None
                
            task_id, task_type, payload_data = task
            
            # Handle JSON parsing securely depending on how psycopg2 returns it
            if isinstance(payload_data, str):
                payload = json.loads(payload_data)
            else:
                payload = payload_data

            # Mark task as running and COMMIT the change
            cur.execute("""
                UPDATE ai_tasks
                SET status = 'running'
                WHERE id = %s
            """, (task_id,))
            conn.commit()
            
            return {
                "id": task_id,
                "task_type": task_type,
                "payload": payload
            }

def mark_task_completed(task_id, result=None):
    """Marks a task as completed and commits it to the DB."""
    with get_pooled_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE ai_tasks
                SET status = 'completed', completed_at = NOW(), result = %s
                WHERE id = %s
            """, (json.dumps(result) if result else None, task_id))
            conn.commit()

def mark_task_failed(task_id, error_msg):
    """Marks a task as failed and logs the error in the DB."""
    with get_pooled_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE ai_tasks
                SET status = 'failed', error = %s
                WHERE id = %s
            """, (error_msg, task_id))
            conn.commit()

def execute_task(task):
    """Routes and executes the task payload."""
    task_id = task["id"]
    task_type = task["task_type"]
    payload = task["payload"]
    
    logging.info(f"[WORKER] Starting task {task_id}: {task_type}")
    
    try:
        # Route to the appropriate script based on task_type
        if task_type == 'scrape_listing':
            result = run_scrape_listing(payload)
            mark_task_completed(task_id, result)
            logging.info(f"[WORKER] Completed task {task_id}")
            
        else:
            raise ValueError(f"Unknown task_type: {task_type}")
            
    except Exception as e:
        error_msg = str(e)
        mark_task_failed(task_id, error_msg)
        logging.error(f"[WORKER] Failed task {task_id}: {error_msg}")

def main():
    logging.info("[WORKER] Production AI task worker online")
    
    while not shutdown_flag:
        try:
            task = fetch_task()
            if task:
                execute_task(task)
            else:
                # Sleep briefly if no pending tasks are found
                time.sleep(2)
        except Exception as e:
            logging.error(f"[WORKER] Unexpected polling error: {str(e)}")
            time.sleep(5)
            
    logging.info("[WORKER] Shutdown complete")
    print("[DB] Connection pool closed.")

if __name__ == "__main__":
    main()