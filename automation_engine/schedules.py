from automation_engine.database import get_connection


def main():

    conn=get_connection()
    cur=conn.cursor()

    cur.execute("""
    SELECT
        id,
        name,
        interval_seconds,
        enabled,
        last_run
    FROM scheduled_tasks
    """)

    for row in cur.fetchall():
        print(row)


if __name__=="__main__":
    main()
