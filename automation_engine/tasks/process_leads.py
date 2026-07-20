import os
import psycopg2

from automation_engine.enrichment import run_enrichment_batch


def fetch_candidate_leads():

    conn = psycopg2.connect(
        os.environ["DATABASE_URL"]
    )

    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            l.id,
            l.address,
            l.city,
            l.status,
            f.project_count,
            f.building_permit_count_24m,
            f.planning_application_count_24m

        FROM leads l

        JOIN prospect_features f
        ON l.id = f.lead_id

        WHERE
            COALESCE(f.project_count,0) > 0
            OR COALESCE(f.building_permit_count_24m,0) > 0
            OR COALESCE(f.planning_application_count_24m,0) > 0

        ORDER BY
            COALESCE(f.project_count,0) DESC,
            COALESCE(f.building_permit_count_24m,0) DESC

        LIMIT 100
        """
    )

    rows = cur.fetchall()

    cur.close()
    conn.close()


    return [
        {
            "id": row[0],
            "address": row[1],
            "city": row[2],
            "status": row[3],
            "project_count": row[4],
            "building_permit_count_24m": row[5],
            "planning_application_count_24m": row[6],
        }
        for row in rows
    ]



def main():

    print(
        "PROCESS LEADS TASK STARTED"
    )


    properties = fetch_candidate_leads()


    print(
        "Candidate leads found:",
        len(properties)
    )


    results = run_enrichment_batch(
        properties
    )


    print(
        "Processed leads:",
        len(results)
    )



if __name__ == "__main__":
    main()
