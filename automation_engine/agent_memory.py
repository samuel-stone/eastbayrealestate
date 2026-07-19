from automation_engine.database import get_connection


def init_memory():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS agent_memory (
        id SERIAL PRIMARY KEY,
        observation TEXT,
        created_at TIMESTAMP DEFAULT NOW()
    )
    """)

    conn.commit()
    cur.close()
    conn.close()



def remember(note):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO agent_memory(observation)
        VALUES(%s)
        """,
        (note,)
    )

    conn.commit()
    cur.close()
    conn.close()



def recall():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM agent_memory
        ORDER BY created_at DESC
        LIMIT 20
    """)

    rows = cur.fetchall()

    conn.close()

    return rows
