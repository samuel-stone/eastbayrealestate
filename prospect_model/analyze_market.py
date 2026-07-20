import os
import psycopg2
from datetime import datetime



def main():

    print(
        "Market Analysis Agent started"
    )


    conn = psycopg2.connect(
        os.environ["DATABASE_URL"]
    )

    cur = conn.cursor()


    cur.execute(
        """
        select
            count(*)
        from leads_sandbox
        """
    )


    properties = cur.fetchone()[0]


    print(
        "Analyzing properties:",
        properties
    )


    # future:
    # price trends
    # inventory
    # neighborhood scoring
    # opportunity ranking


    cur.close()
    conn.close()


    print(
        "Market analysis complete",
        datetime.now()
    )



if __name__ == "__main__":
    main()
