import os
import time
import psycopg2
from psycopg2 import pool
from contextlib import contextmanager

class DatabasePool:
    """Singleton connection pool manager with automatic retry mechanism for high reliability."""
    _pool = None

    @classmethod
    def initialize(cls, minconn=1, maxconn=10):
        if cls._pool is None:
            db_url = os.environ.get("DATABASE_URL")
            if not db_url:
                raise ValueError("DATABASE_URL environment variable is not set.")
            
            # Retry loop for initializing the connection pool if database is waking up
            retries = 3
            for attempt in range(retries):
                try:
                    cls._pool = pool.SimpleConnectionPool(minconn, maxconn, db_url)
                    print("[+] Database connection pool successfully initialized.")
                    break
                except Exception as e:
                    if attempt == retries - 1:
                        raise e
                    print(f"[-] Pool initialization failed (Attempt {attempt+1}/{retries}): {e}. Retrying in 3s...")
                    time.sleep(3)

    @classmethod
    @contextmanager
    def get_connection(cls):
        """Context manager providing a pooled connection with auto-return and error handling."""
        if cls._pool is None:
            cls.initialize()
        
        conn = cls._pool.getconn()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cls._pool.putconn(conn)

def execute_query(query, params=None, fetch=True):
    """Utility runner for queries utilizing the centralized connection pool."""
    with DatabasePool.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            if fetch:
                try:
                    return cur.fetchall()
                except psycopg2.ProgrammingError:
                    return [] # Non-fetching queries like INSERT/UPDATE
            return None