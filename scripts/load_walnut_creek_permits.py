import os
import psycopg2
from datetime import datetime, timedelta


def load_permits(conn):
    print("Loading permit_details...")

    cur = conn.cursor()

    cur.execute("""
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
            p.description,
            p.permit_type,
            p.captured_at,
            p.permit_no,
            p.permit_date
        FROM walnut_creek_permits p
        JOIN leads l
            ON (
                regexp_replace(upper(trim(l.normalized_address)), '[^A-Z0-9]', '', 'g')
                =
                regexp_replace(upper(trim(p.clean_addr)), '[^A-Z0-9]', '', 'g')
            )
            OR (
                -- Fallback to match core street number and primary name tokens if suffixes differ
                split_part(regexp_replace(upper(trim(l.normalized_address)), '[^A-Z0-9 ]', '', 'g'), ' ', 1)
                =
                split_part(regexp_replace(upper(trim(p.clean_addr)), '[^A-Z0-9 ]', '', 'g'), ' ', 1)
                AND
                split_part(regexp_replace(upper(trim(l.normalized_address)), '[^A-Z0-9 ]', '', 'g'), ' ', 2)
                =
                split_part(regexp_replace(upper(trim(p.clean_addr)), '[^A-Z0-9 ]', '', 'g'), ' ', 2)
            )
        ON CONFLICT DO NOTHING;
    """)

    print("Permit rows inserted:", cur.rowcount)

    conn.commit()

    cur.close()


def update_features(conn):
    print("Updating prospect_features...")

    cur = conn.cursor()

    cur.execute("""
        UPDATE prospect_features pf
        SET
            project_count = x.project_count,

            building_permit_count_24m =
                x.building_count,

            planning_application_count_24m =
                x.planning_count,

            major_project_type =
                x.major_project_type,

            updated_at = NOW()

        FROM (

            SELECT
                l.id AS lead_id,

                COUNT(pd.*) AS project_count,

                COUNT(
                    CASE
                        WHEN lower(pd.permit_type)
                             LIKE '%building%'
                        THEN 1
                    END
                ) AS building_count,

                COUNT(
                    CASE
                        WHEN lower(pd.permit_type)
                             LIKE '%planning%'
                        THEN 1
                    END
                ) AS planning_count,


                (
                    SELECT permit_type
                    FROM permit_details pd2
                    WHERE pd2.lead_id = l.id
                    GROUP BY permit_type
                    ORDER BY COUNT(*) DESC
                    LIMIT 1
                ) AS major_project_type


            FROM leads l

            JOIN permit_details pd
                ON pd.lead_id = l.id

            GROUP BY l.id

        ) x

        WHERE pf.lead_id = x.lead_id;

    """)

    print("Prospect rows updated:", cur.rowcount)

    conn.commit()

    cur.close()


def main():

    print("""
===================================
Walnut Creek Permit Feature Loader
===================================
""")

    conn = psycopg2.connect(
        os.environ["DATABASE_URL"]
    )

    try:
        load_permits(conn)
        update_features(conn)

        print("""
===================================
Pipeline completed successfully.
===================================
""")

    finally:
        conn.close()


if __name__ == "__main__":
    main()