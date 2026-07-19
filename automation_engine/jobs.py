from automation_engine.database import get_connection


def add_job(name):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO jobs(name,status) VALUES(%s,'queued')",
        (name,)
    )

    conn.commit()
    cur.close()
    conn.close()

    print("job queued:", name)


if __name__ == "__main__":
    add_job("scrape_listings")
