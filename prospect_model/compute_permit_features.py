import psycopg2
from db_utils import get_db_connection


def update_features():
    print("Recalculating permit counts from deduplicated records...")
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 1. Create an index so the database doesn't have to scan 5 billion times
        print("Building index for lightning-fast counting...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_permit_details_lead_id ON permit_details(lead_id)")
        
        # 2. Reset counts to 0 to ensure a clean slate
        cursor.execute("UPDATE prospect_features SET building_permit_count_24m = 0")
        
        # 3. Count the unique records and update
        print("Crunching the numbers...")
        cursor.execute("""
            UPDATE prospect_features 
            SET building_permit_count_24m = (
                SELECT COUNT(*) 
                FROM permit_details 
                WHERE permit_details.lead_id = prospect_features.lead_id
            )
            WHERE EXISTS (
                SELECT 1 
                FROM permit_details 
                WHERE permit_details.lead_id = prospect_features.lead_id
            )
        """)
        
        conn.commit()
        print("Successfully updated prospect_features with accurate counts!")

if __name__ == "__main__":
    update_features()