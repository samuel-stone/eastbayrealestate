import os
import atexit

from contextlib import contextmanager
from psycopg_pool import ConnectionPool
from dotenv import load_dotenv


load_dotenv()


DATABASE_URL = (
    os.getenv("DATABASE_URL", "postgresql://localhost/eastbayrealestate")
    .replace("postgres://", "postgresql://", 1)
)


_pool = None


def get_pool():

    global _pool

    if _pool is None:

        _pool = ConnectionPool(
            conninfo=DATABASE_URL,
            min_size=1,
            max_size=5,
            timeout=30,
            open=True
        )

    return _pool



@contextmanager
def get_pooled_connection():

    pool = get_pool()

    with pool.connection() as conn:
        yield conn



def close_pool():

    global _pool

    if _pool is not None:

        try:
            _pool.close()
            print("[DB] Connection pool closed.")

        except Exception as e:
            print(
                f"[DB] Pool close warning: {e}"
            )

        finally:
            _pool = None



# Automatically close when scripts terminate
atexit.register(close_pool)