from automation_engine.database import get_connection

def main():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            id,
            name,
            status,
            attempts,
            started_at,
            completed_at,
            created_at
        FROM jobs
        ORDER BY id DESC
        LIMIT 20
    """)

    rows = cur.fetchall()

    for row in rows:
        print(row)

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
