from automation_engine.database import get_connection


def analyze_system():

    conn = get_connection()
    cur = conn.cursor()


    analysis = {
        "jobs": []
    }


    try:

        #
        # Look at system state
        #
        cur.execute(
            """
            SELECT
                name,
                status,
                count(*) as total
            FROM jobs
            GROUP BY name,status
            """
        )

        rows = cur.fetchall()


        print(
            "SYSTEM STATUS:"
        )

        for row in rows:
            print(row)



        #
        # Ensure core pipeline jobs exist
        #
        cur.execute(
            """
            SELECT 1
            FROM jobs
            WHERE name='discover_listings'
            AND status IN ('queued','running')
            LIMIT 1
            """
        )

        discovery_exists = cur.fetchone()



        if not discovery_exists:

            analysis["jobs"].append(
                "discover_listings"
            )



        #
        # Ensure Redfin scraping runs
        #
        cur.execute(
            """
            SELECT 1
            FROM jobs
            WHERE name='scrape_redfin'
            AND status IN ('queued','running')
            LIMIT 1
            """
        )


        scrape_exists = cur.fetchone()


        if not scrape_exists:

            analysis["jobs"].append(
                "scrape_redfin"
            )



        #
        # Ensure enrichment
        #
        cur.execute(
            """
            SELECT 1
            FROM jobs
            WHERE name='process_leads'
            AND status IN ('queued','running')
            LIMIT 1
            """
        )


        enrich_exists = cur.fetchone()


        if not enrich_exists:

            analysis["jobs"].append(
                "process_leads"
            )



    finally:

        cur.close()
        conn.close()



    return analysis