import os
import psycopg2

def migrate_database():
    print("[+] Connecting to live PostgreSQL database to add Seller Motivation schema...")
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    cur = conn.cursor()
    
    # Add marketplace intelligence columns to leads or a dedicated table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS marketplace_signals (
            id SERIAL PRIMARY KEY,
            lead_id INTEGER REFERENCES leads(id) ON DELETE CASCADE,
            days_on_market INTEGER DEFAULT 0,
            original_price NUMERIC,
            current_price NUMERIC,
            price_drop_count INTEGER DEFAULT 0,
            total_price_drop_amount NUMERIC DEFAULT 0,
            listing_status VARCHAR(50) DEFAULT 'active',
            deal_fell_through BOOLEAN DEFAULT FALSE,
            is_fixer_or_tlc BOOLEAN DEFAULT FALSE,
            seller_motivation_score INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    conn.commit()
    cur.close()
    conn.close()
    print("[+] Marketplace signals schema successfully deployed!")

if __name__ == "__main__":
    migrate_database()