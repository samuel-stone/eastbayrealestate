import json
import re
import requests

from db_pool import get_pooled_connection


ZIP_CODES = [
    "94506"
]


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 Chrome/120 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9"
}



# --------------------------------------------------
# Redfin Discovery
# --------------------------------------------------

def discover_redfin(zipcode, limit=100):

    url = f"https://www.redfin.com/zipcode/{zipcode}"

    print("[REDFIN] Fetching:", url)

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=30
        )

        response.raise_for_status()

        html = response.text

    except Exception as e:
        print("[REDFIN] Failed:", e)
        return []


    listings = set()


    matches = re.findall(
        r'https://www\.redfin\.com/[^"]+/home/\d+',
        html
    )


    for url in matches:

        url = url.replace("\\/", "/")


        # MUST be California
        if "/CA/" not in url:
            continue


        # MUST contain target zipcode
        if zipcode not in url:
            continue


        # reject NY
        bad = [
            "/NY/",
            "new-york",
            "brooklyn",
            "queens",
            "manhattan"
        ]


        if any(
            x.lower() in url.lower()
            for x in bad
        ):
            continue


        listings.add(url)



    results = list(listings)


    print(
        f"[REDFIN] Valid {zipcode} listings:",
        len(results)
    )


    return results[:limit]

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



            cur.execute(
                """
                SELECT id
                FROM ai_tasks
                WHERE task_type='scrape_listing'
                AND payload->>'url'=%s
                AND status IN
                (
                    'pending',
                    'running',
                    'completed'
                )
                LIMIT 1
                """,
                (
                    url,
                )
            )



            if cur.fetchone():

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
                    retry_count,
                    priority
                )

                VALUES
                (
                    'scrape_listing',
                    %s,
                    'pending',
                    0,
                    5
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
            zipcode,
            limit=1
        )



        for url in listings:


            if enqueue_listing(url):

                total += 1




    print(
        f"Discovery complete. Added {total} tasks."
    )




if __name__ == "__main__":

    main()