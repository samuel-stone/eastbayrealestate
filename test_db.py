import psycopg2

# Replace this with your actual connection string
DATABASE_URL = "os.getenv("DATABASE_URL")"

def test_connection():
    try:
        # Establish connection
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # Run a simple query
        cur.execute("SELECT COUNT(*) FROM leads;")
        count = cur.fetchone()[0]
        
        print(f"Success! Connected to Aiven. Total leads in database: {count}")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    test_connection()