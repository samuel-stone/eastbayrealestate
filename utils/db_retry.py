import functools
import time
import psycopg2
from psycopg2 import OperationalError

def retry_on_db_drop(max_retries=3, delay=2):
    """Decorator to retry database operations if the connection drops or shuts down."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            current_delay = delay
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except (OperationalError, psycopg2.InterfaceError) as e:
                    retries += 1
                    print(f"[!] Database connection lost ({e}). Retrying attempt {retries}/{max_retries} in {current_delay}s...")
                    if retries >= max_retries:
                        raise
                    time.sleep(current_delay)
                    current_delay *= 2  # Exponential backoff
        return wrapper
    return decorator
