from automation_engine.database import get_connection


def failed_jobs():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT name, attempts, last_error
        FROM jobs
        WHERE status='failed'
        ORDER BY created_at DESC
        LIMIT 10
    """)

    rows = cur.fetchall()

    conn.close()

    return rows



def recent_jobs():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT name,status,created_at
        FROM jobs
        ORDER BY created_at DESC
        LIMIT 10
    """)

    rows = cur.fetchall()

    conn.close()

    return rows
