import os
import json
import time
import subprocess
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def execute_script_task(task_id, payload):
    """Executes standard Python web scrapers via subprocess"""
    command = payload.get("command")
    print(f"[Task {task_id}] Executing dynamic command: {command}")
    subprocess.run(command.split(), check=True)

def execute_agent_objective(task_id, payload):
    """Placeholder for future LLM Agent logic"""
    goal = payload.get("goal")
    print(f"[Task {task_id}] Received AI Objective: {goal}")
    print(f"[Task {task_id}] Objective processing complete.")

def poll_queue():
    print("Worker started. Listening for tasks...")
    while True:
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT id, task_type, payload 
                        FROM ai_tasks 
                        WHERE status = 'pending' 
                        ORDER BY priority ASC, created_at ASC 
                        LIMIT 1 
                        FOR UPDATE SKIP LOCKED;
                    """)
                    task = cur.fetchone()

                    if task:
                        task_id = task['id']
                        task_type = task['task_type']
                        
                        payload = task['payload']
                        if isinstance(payload, str):
                            payload = json.loads(payload)

                        print(f"\n--- Processing Task {task_id} ({task_type}) ---")
                        
                        cur.execute("UPDATE ai_tasks SET status = 'in_progress' WHERE id = %s", (task_id,))
                        conn.commit()

                        try:
                            if task_type == "execute_script":
                                execute_script_task(task_id, payload)
                            elif task_type == "agent_objective":
                                execute_agent_objective(task_id, payload)
                            else:
                                print(f"[Task {task_id}] Unknown task type: {task_type}")

                            cur.execute("UPDATE ai_tasks SET status = 'completed' WHERE id = %s", (task_id,))
                            conn.commit()
                            print(f"[Task {task_id}] Successfully completed.")

                        except Exception as e:
                            print(f"[Task {task_id}] Failed with error: {e}")
                            cur.execute("UPDATE ai_tasks SET status = 'failed' WHERE id = %s", (task_id,))
                            conn.commit()
            
        except Exception as db_err:
            print(f"Database connection error: {db_err}")
            
        time.sleep(10)

if __name__ == "__main__":
    poll_queue()
