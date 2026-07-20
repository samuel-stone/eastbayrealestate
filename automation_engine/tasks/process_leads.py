import os
import psycopg2

from automation_engine.enrichment import run_enrichment_batch


def fetch_candidate_leads():
    conn = psycopg2.connect(
        os.environ["DATABASE_URL"]
    )
    cur = conn.cursor()

    # Added l.status filter and grouped the OR conditions
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
        JOIN prospect_features f ON l.id = f.lead_id
        WHERE 
            l.status = 'new' AND
            (
                COALESCE(f.project_count,0) > 0
                OR COALESCE(f.building_permit_count_24m,0) > 0
                OR COALESCE(f.planning_application_count_24m,0) > 0
            )
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


def update_leads_status(lead_ids, new_status="processed"):
    if not lead_ids:
        return
        
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    cur = conn.cursor()
    
    # Update all processed IDs in one transaction
    cur.execute(
        "UPDATE leads SET status = %s WHERE id = ANY(%s)",
        (new_status, lead_ids)
    )
    
    conn.commit()
    cur.close()
    conn.close()


def main():
    print("PROCESS LEADS TASK STARTED")
    
    properties = fetch_candidate_leads()
    print("Candidate leads found:", len(properties))

    if not properties:
        print("No new leads to process. Exiting.")
        return

    results = run_enrichment_batch(properties)
    print("Processed leads:", len(results))

    # Extract IDs from the successful batch and update DB
    lead_ids = [p["id"] for p in properties]
    update_leads_status(lead_ids, "processed")
    print("Database updated successfully.")


if __name__ == "__main__":
    main()