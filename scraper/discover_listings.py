import os
import json
import re
import sys

import psycopg2
from dotenv import load_dotenv


# --------------------------------------------------
# ENV
# --------------------------------------------------

load_dotenv()


DATABASE_URL = os.getenv(
    "DATABASE_URL"
)


if not DATABASE_URL:

    print(
        "DATABASE_URL missing"
    )

    sys.exit(1)



# --------------------------------------------------
# DATABASE
# --------------------------------------------------

def get_connection():

    return psycopg2.connect(
        DATABASE_URL
    )



# --------------------------------------------------
# DISCOVERY
# --------------------------------------------------

ZIP_CODES = [
    "94506"
]



def discover_redfin(zip_code):

    """
    Temporary discovery source.

    Later this becomes:
    Redfin API
    MLS feed
    Zillow
    County records
    """

    print(
        f"Exploring ZIP: {zip_code}"
    )


    # Current known extraction format
    urls = [

        "https://www.redfin.com/CA/Danville/2057-Drysdale-St-94506/home/56909566",

        "https://www.redfin.com/CA/Danville/2962-Deer-Meadow-Dr-94506/home/755033",

        "https://www.redfin.com/CA/Danville/5032-Enderby-St-94506/home/40091203"

    ]


    return urls



# --------------------------------------------------
# QUEUE
# --------------------------------------------------

def enqueue_listing(url):


    payload = {

        "url": url,

        "source": "redfin",

        "task":
            "scrape_listing"

    }



    conn = get_connection()

    cur = conn.cursor()



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

    cur.close()

    conn.close()



    print(
        "Queued:",
        url
    )



# --------------------------------------------------
# MAIN
# --------------------------------------------------

def main():


    total = 0


    for zipcode in ZIP_CODES:


        listings = discover_redfin(
            zipcode
        )


        for url in listings:

            enqueue_listing(
                url
            )

            total += 1



    print(
        f"Discovery complete. Added {total} tasks."
    )



if __name__ == "__main__":

    main()