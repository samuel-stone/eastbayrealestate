import os
import pandas as pd
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def persist_strategies():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("[-] DATABASE_URL not set.")
        return

    csv_file = "hybrid_geometric_genai_leads.csv"
    if not os.path.exists(csv_file):
        print(f"[-] {csv_file} not found.")
        return

    df = pd.read_csv(csv_file)
    conn = psycopg2.connect(db_url)
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS geometric_strategy_audit (
                    id SERIAL PRIMARY KEY,
                    address TEXT UNIQUE,
                    city TEXT,
                    building_permit_count_24m INT,
                    major_project_type TEXT,
                    distance_from_hub_miles FLOAT,
                    geometric_route_rank INT,
                    ai_route_strategy TEXT,
                    ai_valuation_strategy TEXT,
                    execution_audit TEXT,
                    updated_at TIMESTAMP DEFAULT NOW()
                );
            """)
            conn.commit()

            count = 0
            for _, row in df.iterrows():
                cur.execute("""
                    INSERT INTO geometric_strategy_audit 
                    (address, city, building_permit_count_24m, major_project_type, distance_from_hub_miles, geometric_route_rank, ai_route_strategy, ai_valuation_strategy, execution_audit, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (address) DO UPDATE SET
                        building_permit_count_24m = EXCLUDED.building_permit_count_24m,
                        major_project_type = EXCLUDED.major_project_type,
                        distance_from_hub_miles = EXCLUDED.distance_from_hub_miles,
                        geometric_route_rank = EXCLUDED.geometric_route_rank,
                        ai_route_strategy = EXCLUDED.ai_route_strategy,
                        ai_valuation_strategy = EXCLUDED.ai_valuation_strategy,
                        execution_audit = EXCLUDED.execution_audit,
                        updated_at = NOW();
                """, (
                    row.get('address'),
                    row.get('city', 'Walnut Creek'),
                    int(row.get('building_permit_count_24m', 0)),
                    row.get('major_project_type', ''),
                    float(row.get('distance_from_hub_miles', 0.0)),
                    int(row.get('geometric_route_rank', 1)),
                    row.get('ai_route_strategy', ''),
                    row.get('ai_valuation_strategy', ''),
                    row.get('execution_audit', '')
                ))
                count += 1
            conn.commit()
            print(f"[+] Successfully persisted {count} hybrid geometric strategies to PostgreSQL!")
    finally:
        conn.close()

if __name__ == "__main__":
    persist_strategies()
