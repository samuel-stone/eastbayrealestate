import os
import json
import psycopg2

def get_db_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

def write_to_memory(payload: dict):
    """
    Writes structured findings to the agent_memory table's JSONB column.
    """
    source_agent = payload.get("source_agent", "single_reviewer")
    
    # Package the commit details into the observation JSON
    observation_data = {
        "type": "commit_review",
        "commit_sha": payload.get("commit_sha"),
        "diff": payload.get("diff"),
        "summary": payload.get("summary")
    }

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO agent_memory (observation, source_agent)
                VALUES (%s, %s)
            """, (
                json.dumps(observation_data),
                source_agent
            ))
        conn.commit()
    except Exception as e:
        print(f"Failed to write to memory: {e}")
        conn.rollback()
    finally:
        conn.close()