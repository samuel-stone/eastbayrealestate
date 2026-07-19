import psycopg2, os, sys
sys.path.append(os.getcwd())

def enqueue_job():
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()
    cur.execute("INSERT INTO ai_tasks (task_type, payload) VALUES ('health_check', '{\"check\": \"daily\"}')")
    conn.commit()
    cur.close()
    conn.close()
    print("Scheduler: Job enqueued.")

if __name__ == "__main__":
    enqueue_job()