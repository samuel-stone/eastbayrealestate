import os
import json
import time
import psycopg2
from google import genai
from google.genai import types

# Initialize GenAI Client
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def get_db_connection():
    return psycopg2.connect(os.environ['DATABASE_URL'])

def process_task_queue():
    """Polls the ai_tasks table and executes pending tasks."""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Select next pending task
    cur.execute("SELECT id, task_type, payload FROM ai_tasks WHERE status = 'pending' ORDER BY created_at ASC LIMIT 1;")
    task = cur.fetchone()
    
    if task:
        task_id, task_type, payload = task
        print(f"Processing task {task_id}: {task_type}")
        
        try:
            # Logic for your specific agent tasks
            # e.g., if task_type == 'health_check': ...
            cur.execute("UPDATE ai_tasks SET status = 'completed' WHERE id = %s", (task_id,))
        except Exception as e:
            print(f"Error processing task {task_id}: {e}")
            cur.execute("UPDATE ai_tasks SET status = 'failed', retry_count = retry_count + 1 WHERE id = %s", (task_id,))
            
        conn.commit()
    
    cur.close()
    conn.close()

def analyze_system(system_data):
    """Main brain entry point for system analysis."""
    response = client.models.generate_content(
        model='gemini-2.0-flash',
        contents=f"Analyze this system data: {system_data}"
    )
    return response.text