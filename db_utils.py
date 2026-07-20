import os
import psycopg2

def get_db_connection():
    # Fetch from environment variable, default to None to force you to set it
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        raise ValueError("DATABASE_URL environment variable is not set!")
    return psycopg2.connect(db_url, connect_timeout=10)

def upsert_lead(normalized_address, city, address, parcel_number, assessed_value, status="New"):
    """
    Inserts a new lead or updates/ignores if the normalized_address already exists.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO leads (normalized_address, city, address, parcel_number, assessed_value, status, first_seen_at, last_seen_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
                ON CONFLICT (normalized_address) 
                DO UPDATE SET 
                    last_seen_at = NOW(),
                    assessed_value = EXCLUDED.assessed_value
                RETURNING id;
                """,
                (normalized_address, city, address, parcel_number, assessed_value, status)
            )
            lead_id = cur.fetchone()[0]
            conn.commit()
            return lead_id
    finally:
        conn.close()
