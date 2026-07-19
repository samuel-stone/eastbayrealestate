import os
from automation_engine.database import get_connection


def main():

    print("East Bay Automation Health Check")

    print(
        "DATABASE_URL:",
        "connected" if os.getenv("DATABASE_URL") else "missing"
    )

    conn = get_connection()

    cur = conn.cursor()

    cur.execute(
        "SELECT NOW();"
    )

    print(
        "Database time:",
        cur.fetchone()
    )

    conn.close()

    print("Health OK")


if __name__ == "__main__":
    main()
