import psycopg2
from config.config import Registry

DB_URL = Registry.get_db_url()


def get_db_connection():
    return psycopg2.connect(DB_URL, sslmode="require")


def run_pipeline():
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        print("Loading permit_details...")

        cursor.execute("""
            INSERT INTO permit_details (
                lead_id,
                description,
                permit_type,
                date_processed,
                permit_number,
                issued_date
            )
            SELECT
                l.id,
                w.description,
                w.permit_type,
                NOW(),
                w.permit_no,
                w.permit_date
            FROM walnut_creek_permits w
            JOIN leads l
              ON UPPER(TRIM(l.normalized_address)) = UPPER(TRIM(w.clean_addr))
            ON CONFLICT (permit_number) DO NOTHING;
        """)

        print(f"Permit rows inserted: {cursor.rowcount:,}")

        print("Updating prospect_features...")

        cursor.execute("""
            INSERT INTO prospect_features (
                lead_id,
                project_count
            )
            SELECT
                l.id,
                COUNT(*)
            FROM walnut_creek_permits w
            JOIN leads l
              ON UPPER(TRIM(l.normalized_address)) = UPPER(TRIM(w.clean_addr))
            GROUP BY l.id
            ON CONFLICT (lead_id)
            DO UPDATE
            SET project_count = EXCLUDED.project_count;
        """)

        print(f"Prospect rows updated: {cursor.rowcount:,}")

        conn.commit()

        print("\n===================================")
        print("Pipeline completed successfully.")
        print("===================================")

    except Exception as e:
        conn.rollback()
        print(f"Pipeline failed: {e}")
        raise

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    run_pipeline()