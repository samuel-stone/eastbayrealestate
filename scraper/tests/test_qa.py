# test_qa.py
from config.config import Registry

def test_config():
    # Verify Registry can load configuration
    sources = Registry.load_sources()
    assert "sources" in sources, "sources.json missing 'sources' key"
    print("✓ Registry loaded successfully.")

    # Verify Database Connection
    from scripts.load_walnut_creek_permits import get_db_connection
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1")
    assert cursor.fetchone() == (1,)
    print("✓ Database connection verified.")
    cursor.close()
    conn.close()

if __name__ == "__main__":
    test_config()
