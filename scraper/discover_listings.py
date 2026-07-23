import json

from db_pool import get_pooled_connection


ZIP_CODES = [
    "94506"
]


# --------------------------------------------------
# Redfin Discovery
# --------------------------------------------------

def discover_redfin(zipcode):
    """
    Temporary Redfin discovery source.

    Replace with live Redfin search extraction later.
    """

    return [
        "https://www.redfin.com/CA/Danville/2057-Drysdale-St-94506/home/56909566",
        "https://www.redfin.com/CA/Danville/2962-Deer-Meadow-Dr-94506/home/755033",
        "https://www.redfin.com/CA/Danville/5032-Enderby-St-94506/home/40091203"
    ]


# --------------------------------------------------
# Queue
# --------------------------------------------------

def enqueue_listing(url):

    payload = {
        "url": url,
        "source": "redfin",
        "task": "scrape_listing"
    }


    with get_pooled_connection() as conn:

        with conn.cursor() as cur:

            # Prevent duplicate tasks including completed work
            cur.execute(
                """
                SELECT id
                FROM ai_tasks
                WHERE task_type = 'scrape_listing'
                AND payload->>'url' = %s
                AND status IN (
                    'pending',
                    'queued',
                    'running',
                    'completed'
                )
                LIMIT 1
                """,
                (
                    url,
                )
            )


            existing = cur.fetchone()


            if existing:

                print(
                    "Already queued:",
                    url
                )

                return False


            cur.execute(
                """
                INSERT INTO ai_tasks
                (
                    task_type,
                    payload,
                    status,
                    retry_count
                )

                VALUES
                (
                    'scrape_listing',
                    %s,
                    'pending',
                    0
                )
                """,
                (
                    json.dumps(payload),
                )
            )


        conn.commit()


    print(
        "Queued:",
        url
    )


    return True



# --------------------------------------------------
# Main
# --------------------------------------------------

def main():

    total = 0


    for zipcode in ZIP_CODES:

        print(
            "Exploring ZIP:",
            zipcode
        )


        listings = discover_redfin(
            zipcode
        )


        for url in listings:

            if enqueue_listing(url):

                total += 1



    print(
        f"Discovery complete. Added {total} new tasks."
    )



if __name__ == "__main__":

    main()
