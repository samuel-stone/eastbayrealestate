import os
import psycopg2
from automation_engine.enrichment import run_enrichment_batch


def get_candidate_properties(conn, limit=100):

    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            l.id,
            l.address,
            l.city,
            l.status,
            pf.project_count,
            pf.building_permit_count_24m,
            pf.planning_application_count_24m
        FROM leads l
        JOIN prospect_features pf
            ON pf.lead_id = l.id
        WHERE
            l.status = 'new'
        AND (
            pf.project_count > 0
            OR pf.building_permit_count_24m > 0
        )
        ORDER BY
            pf.project_count DESC
        LIMIT %s
        """,
        (limit,)
    )

    rows = cur.fetchall()

    cur.close()

    return [
        {
            "id": r[0],
            "address": r[1],
            "city": r[2],
            "status": r[3],
            "project_count": r[4],
            "building_permit_count_24m": r[5],
            "planning_application_count_24m": r[6],
        }
        for r in rows
    ]


def main():

    print("ENRICH PROPERTIES TASK STARTED")

    conn = psycopg2.connect(
        os.environ["DATABASE_URL"]
    )

    properties = get_candidate_properties(conn)

    print(
        "Candidate properties found:",
        len(properties)
    )

    for p in properties:
        print("Enriching:", p)

    results = run_enrichment_batch(properties)

    print(
        "Enriched properties:",
        len(results)
    )

    conn.close()


if __name__ == "__main__":
    main()