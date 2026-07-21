import os
import psycopg2

def get_db_connection():
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        raise ValueError("DATABASE_URL environment variable is not set!")
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    return psycopg2.connect(db_url, connect_timeout=10)

def upsert_lead(normalized_address, city, address, parcel_number, assessed_value, status="Active"):
    """
    Inserts a new lead or updates existing if the normalized_address already exists,
    preserving non-null existing data via COALESCE, and returns the lead ID.
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
                    city = COALESCE(EXCLUDED.city, leads.city),
                    address = COALESCE(EXCLUDED.address, leads.address),
                    assessed_value = COALESCE(EXCLUDED.assessed_value, leads.assessed_value),
                    parcel_number = COALESCE(EXCLUDED.parcel_number, leads.parcel_number),
                    status = COALESCE(EXCLUDED.status, leads.status)
                RETURNING id;
                """,
                (normalized_address, city, address, parcel_number, assessed_value, status)
            )
            result = cur.fetchone()
            conn.commit()
            return result[0] if result else None
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()