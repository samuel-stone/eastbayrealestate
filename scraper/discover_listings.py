import json
import re

import requests

from db_pool import get_pooled_connection


ZIP_CODES = [
    "94506"
]


HEADERS = {
    "User-Agent":
        "Mozilla/5.0",
    "Accept-Language":
        "en-US,en;q=0.9"
}



def discover_redfin(zipcode):

    url = (
        f"https://www.redfin.com/zipcode/{zipcode}"
    )

    print(
        "[REDFIN] Fetching:",
        url
    )


    r = requests.get(
        url,
        headers=HEADERS,
        timeout=30
    )


    html = r.text


    listings = []


    # Redfin embedded listing URLs

    matches = re.findall(
        r'https://www\.redfin\.com/CA/[^"]+/home/\d+',
        html
    )


    for u in matches:

        if zipcode in u:

            listings.append(
                u
            )


    # Remove duplicates

    listings = list(
        dict.fromkeys(listings)
    )


    print(
        "[REDFIN] Found:",
        len(listings)
    )


    return listings




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
                LIMIT 1
                """,
                (
                    url,
                )
            )


            if cur.fetchone():

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




def main():

    total = 0


    for zipcode in ZIP_CODES:

        listings = discover_redfin(
            zipcode
        )


        for url in listings:

            if enqueue_listing(url):

                total += 1


    print(
        "Added:",
        total
    )



if __name__ == "__main__":
    main()
