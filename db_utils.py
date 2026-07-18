import os
import psycopg2

def get_db_connection():
    # Aiven connection string
    db_url = os.getenv('DATABASE_URL', 'postgres://avnadmin:@pg-305dd876-eastbayrealestate.l.aivencloud.com:22742/defaultdb?sslmode=require')
    return psycopg2.connect(db_url, connect_timeout=10)
