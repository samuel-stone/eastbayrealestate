import os
from psycopg_pool import ConnectionPool
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/eastbayrealestate").replace("postgres://", "postgresql://", 1)

# Initialize connection pool for high-throughput permit ingestion across 364k+ leads
pool = ConnectionPool(conninfo=DATABASE_URL, min_size=2, max_size=10, timeout=30)

def get_pooled_connection():
    """Context manager or direct connection grabber from the enterprise pool."""
    return pool.connection()
