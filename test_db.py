import os
import psycopg2

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL environment variable is missing"
    )

conn = psycopg2.connect(DATABASE_URL)

print("Database connection successful")

conn.close()
