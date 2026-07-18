from db_utils import get_db_connection

def verify():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Test 1: Check connection
        cur.execute("SELECT version();")
        version = cur.fetchone()
        print(f"Connection successful! PostgreSQL version: {version[0]}")
        
        # Test 2: Check row count in the leads table
        cur.execute("SELECT COUNT(*) FROM leads;")
        count = cur.fetchone()[0]
        print(f"Data migration successful: Found {count} rows in 'leads' table.")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Verification failed: {e}")

if __name__ == "__main__":
    verify()
