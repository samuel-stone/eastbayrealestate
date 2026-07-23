import os
import socket
from datetime import datetime

import psycopg2
import psycopg2.extras

from dotenv import load_dotenv

load_dotenv()


WORKER_ID = socket.gethostname()


def get_connection():
    """
    PostgreSQL connection factory.
    Returns dictionary rows.
    """

    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError(
            "DATABASE_URL missing"
        )

    return psycopg2.connect(
        database_url,
        cursor_factory=psycopg2.extras.RealDictCursor
    )


# ============================================================
# Schema
# ============================================================

def init_db():

    conn = get_connection()

    try:
        with conn.cursor() as cur:

            cur.execute("""
            CREATE TABLE IF NOT EXISTS jobs (

                id SERIAL PRIMARY KEY,

                name TEXT NOT NULL,

                status TEXT DEFAULT 'queued',

                attempts INTEGER DEFAULT 0,

                worker_id TEXT,

                created_at TIMESTAMP DEFAULT NOW(),

                started_at TIMESTAMP,

                completed_at TIMESTAMP,

                heartbeat_at TIMESTAMP,

                next_attempt_at TIMESTAMP DEFAULT NOW(),

                result JSONB DEFAULT '{}'::jsonb,

                last_error TEXT

            );
            """)


            cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_jobs_queue
            ON jobs(status, created_at)
            WHERE status='queued';
            """)


            cur.execute("""
            CREATE TABLE IF NOT EXISTS execution_events (

                id SERIAL PRIMARY KEY,

                job_id INTEGER REFERENCES jobs(id),

                event_type TEXT NOT NULL,

                message TEXT,

                metadata JSONB DEFAULT '{}'::jsonb,

                created_at TIMESTAMP DEFAULT NOW()

            );
            """)


        conn.commit()

    finally:
        conn.close()



# ============================================================
# Job creation
# ============================================================

def add_job(name):

    conn = get_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
            INSERT INTO jobs(name)
            VALUES(%s)
            RETURNING *
            """,
            (name,)
            )

            job = cur.fetchone()


        conn.commit()

        return job


    finally:
        conn.close()



# ============================================================
# Atomic worker claim
# ============================================================

def get_job():

    conn = get_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
            UPDATE jobs

            SET

                status='running',

                worker_id=%s,

                started_at=NOW(),

                heartbeat_at=NOW(),

                attempts=attempts+1


            WHERE id = (

                SELECT id

                FROM jobs

                WHERE status='queued'

                AND next_attempt_at <= NOW()

                ORDER BY created_at

                LIMIT 1

                FOR UPDATE SKIP LOCKED

            )

            RETURNING *

            """,
            (WORKER_ID,)
            )


            job = cur.fetchone()


        conn.commit()

        return job


    finally:

        conn.close()



# ============================================================
# Heartbeat
# ============================================================

def heartbeat(job_id):

    conn = get_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
            UPDATE jobs

            SET heartbeat_at=NOW()

            WHERE id=%s

            """,
            (job_id,)
            )


        conn.commit()

    finally:

        conn.close()



# ============================================================
# Completion
# ============================================================

def complete_job(
    job_id,
    result
):

    conn = get_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
            UPDATE jobs

            SET

                status='completed',

                completed_at=NOW(),

                result=%s,

                last_error=NULL


            WHERE id=%s

            """,
            (
                psycopg2.extras.Json(result),
                job_id
            )
            )


        conn.commit()


    finally:

        conn.close()



# ============================================================
# Failure + retry
# ============================================================

def fail_job(
    job_id,
    error
):

    conn = get_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
            UPDATE jobs

            SET

                status =
                CASE

                    WHEN attempts < 3
                    THEN 'queued'

                    ELSE 'failed'

                END,


                next_attempt_at =
                CASE

                    WHEN attempts < 3
                    THEN NOW() + INTERVAL '5 minutes'

                    ELSE NULL

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



# ============================================================
# Telemetry
# ============================================================

def log_event(
    job_id,
    event_type,
    message,
    metadata=None
):

    conn = get_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
            INSERT INTO execution_events(

                job_id,
                event_type,
                message,
                metadata

            )

            VALUES(%s,%s,%s,%s)

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