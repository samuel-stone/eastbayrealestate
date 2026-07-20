import os
import psycopg2

def get_db_connection():
    # Fetch from environment variable, default to None to force you to set it
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        raise ValueError("DATABASE_URL environment variable is not set!")
    return psycopg2.connect(db_url, connect_timeout=10)
def upsert_scraped_property(property_address, price, category):
    """
    Inserts a scraped property or skips if the address already exists.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO scraped_property_data (property_address, price, category, created_at)
                VALUES (%s, %s, %s, NOW())
                ON CONFLICT (property_address) DO NOTHING
                RETURNING id;
                """,
                (property_address, price, category)
            )
            inserted_id = cur.fetchone()
            conn.commit()
            return inserted_id is not None
    finally:
        conn.close()
