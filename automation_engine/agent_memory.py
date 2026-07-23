from automation_engine.database import get_connection
import json


def init_memory():
    """
    Initialize shared AI agent memory table.

    Uses JSONB because multi-agent systems need:
    - source_agent tracking
    - structured findings
    - evidence fields
    - confidence scores
    """

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS agent_memory (
        id SERIAL PRIMARY KEY,
        observation JSONB NOT NULL,
        status TEXT DEFAULT 'pending',
        execution_output TEXT,
        created_at TIMESTAMP DEFAULT NOW()
    )
    """)

    conn.commit()

    cur.close()
    conn.close()



def remember(note, source_agent="system"):
    """
    Store structured agent observations.

    Accepts either:
    - dict objects
    - plain strings (converted safely)
    """

    if isinstance(note, str):
        observation = {
            "type": "note",
            "source_agent": source_agent,
            "summary": note
        }
    else:
        observation = note
        observation.setdefault(
            "source_agent",
            source_agent
        )


    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO agent_memory
        (
            observation,
            status
        )
        VALUES
        (
            %s,
            'pending'
        )
        """,
        (
            json.dumps(
                observation,
                ensure_ascii=False
            ),
        )
    )

    conn.commit()

    cur.close()
    conn.close()



def recall(limit=20):
    """
    Retrieve recent agent memory records.
    """

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            id,
            observation,
            status,
            created_at
        FROM agent_memory
        ORDER BY created_at DESC
        LIMIT %s
        """,
        (limit,)
    )

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return rows