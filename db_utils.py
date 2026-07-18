import os
import psycopg2

def get_db_connection():
    # Fetch from environment variable, default to None to force you to set it
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        raise ValueError("DATABASE_URL environment variable is not set!")
    return psycopg2.connect(db_url, connect_timeout=10)