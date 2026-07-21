import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    return psycopg2.connect(
        os.environ["DATABASE_URL"],
        cursor_factory=psycopg2.extras.RealDictCursor
    )


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            status TEXT DEFAULT 'queued',
            attempts INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT NOW(),
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            last_error TEXT
        )
    """)

    conn.commit()
    cur.close()
    conn.close()


def add_job(name):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO jobs(name)
        VALUES(%s)
        RETURNING id
        """,
        (name,)
    )

    job_id = cur.fetchone()["id"]

    conn.commit()
    cur.close()
    conn.close()

    return job_id


def get_job():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM jobs
        WHERE status = 'queued'
        ORDER BY created_at
        LIMIT 1
        FOR UPDATE SKIP LOCKED
        """
    )

    job = cur.fetchone()

    if job:
        cur.execute(
            """
            UPDATE jobs
            SET
                status = 'running',
                started_at = NOW(),
                attempts = attempts + 1
            WHERE id = %s
            """,
            (job["id"],)
        )

        conn.commit()

    cur.close()
    conn.close()

    return job


def complete_job(job_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE jobs
        SET
            status = 'completed',
            completed_at = NOW(),
            last_error = NULL
        WHERE id = %s
        """,
        (job_id,)
    )

    conn.commit()
    cur.close()
    conn.close()


def fail_job(job_id, error):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE jobs
        SET
            status =
                CASE
                    WHEN attempts < 3 THEN 'queued'
                    ELSE 'failed'
                END,
            last_error = %s
        WHERE id = %s
        """,
        (str(error), job_id)
    )

    conn.commit()
    cur.close()
    conn.close()


def clear_completed_jobs(days=30):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        DELETE FROM jobs
        WHERE status = 'completed'
        AND completed_at < NOW() - INTERVAL '%s days'
        """,
        (days,)
    )

    deleted = cur.rowcount

    conn.commit()
    cur.close()
    conn.close()

    return deleted