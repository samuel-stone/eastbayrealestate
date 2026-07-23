import os
import psycopg2
import psycopg2.extras

from dotenv import load_dotenv

load_dotenv()


def get_connection():
    """
    Creates PostgreSQL connection.
    Returns rows as dictionaries.
    """

    database_url = os.environ.get("DATABASE_URL")

    if not database_url:
        raise RuntimeError(
            "DATABASE_URL environment variable is missing."
        )

    return psycopg2.connect(
        database_url,
        cursor_factory=psycopg2.extras.RealDictCursor
    )


def init_db():
    """
    Initialize automation engine tables.
    """

    conn = get_connection()

    try:
        with conn.cursor() as cur:

            cur.execute(
                """
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
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS execution_events (
                    id SERIAL PRIMARY KEY,
                    job_id INTEGER REFERENCES jobs(id),
                    event_type TEXT NOT NULL,
                    message TEXT,
                    metadata JSONB DEFAULT '{}'::jsonb,
                    created_at TIMESTAMP DEFAULT NOW()
                )
                """
            )

        conn.commit()

    finally:
        conn.close()



def add_job(name):
    """
    Add a queued job.
    """

    conn = get_connection()

    try:

        with conn.cursor() as cur:

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

        return job_id

    finally:
        conn.close()



def get_job():
    """
    Atomically claim next queued job.
    Prevents duplicate workers.
    """

    conn = get_connection()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT *
                FROM jobs
                WHERE status='queued'
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
                        status='running',
                        started_at=NOW(),
                        attempts=attempts+1
                    WHERE id=%s
                    """,
                    (job["id"],)
                )


        conn.commit()

        return job

    finally:
        conn.close()



def complete_job(job_id):
    """
    Mark job successful.
    """

    conn = get_connection()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                UPDATE jobs
                SET
                    status='completed',
                    completed_at=NOW(),
                    last_error=NULL
                WHERE id=%s
                """,
                (job_id,)
            )

        conn.commit()

    finally:
        conn.close()



def fail_job(job_id, error):
    """
    Retry failed jobs up to three times.
    """

    conn = get_connection()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                UPDATE jobs
                SET
                    status =
                    CASE
                        WHEN attempts < 3
                        THEN 'queued'
                        ELSE 'failed'
                    END,
                    last_error=%s
                WHERE id=%s
                """,
                (
                    str(error),
                    job_id
                )
            )

        conn.commit()

    finally:
        conn.close()



def clear_completed_jobs(days=30):
    """
    Remove old completed jobs.
    """

    conn = get_connection()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                DELETE FROM jobs
                WHERE status='completed'
                AND completed_at <
                    NOW() - (%s || ' days')::interval
                """,
                (days,)
            )

            deleted = cur.rowcount


        conn.commit()

        return deleted

    finally:
        conn.close()



def log_event(
    job_id,
    event_type,
    message,
    metadata=None
):
    """
    Write execution telemetry.
    Worker owns lifecycle logging.
    """

    conn = get_connection()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                INSERT INTO execution_events(
                    job_id,
                    event_type,
                    message,
                    metadata
                )
                VALUES(
                    %s,
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    job_id,
                    event_type,
                    message,
                    psycopg2.extras.Json(
                        metadata or {}
                    )
                )
            )

        conn.commit()

    finally:
        conn.close()