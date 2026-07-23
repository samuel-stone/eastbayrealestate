import os
import psycopg2

DATABASE_URL = os.getenv("DATABASE_URL")

def process_pending():
    if not DATABASE_URL:
        print("[!] DATABASE_URL is not set.")
        return
        
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    cur.execute("SELECT id, task_type, payload FROM ai_tasks WHERE status = 'pending' LIMIT 5;")
    pending = cur.fetchall()
    
    print(f"Found {len(pending)} sample pending tasks:")
    for task in pending:
        print(task)
        
    cur.close()
    conn.close()

if __name__ == "__main__":
    process_pending()
