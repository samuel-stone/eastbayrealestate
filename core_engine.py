import os
import time
import logging
import psycopg2
from psycopg2 import pool
from contextlib import contextmanager


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)


class DatabasePool:
    """
    Production PostgreSQL connection pool manager.

    Features:
    - Singleton connection pool
    - Automatic initialization
    - Retry handling
    - Connection health checks
    - Transaction safety
    - Automatic connection return
    """

    _pool = None


    @classmethod
    def initialize(cls, minconn=1, maxconn=10):
        """
        Initialize PostgreSQL connection pool.
        """

        if cls._pool is not None:
            return


        db_url = os.environ.get(
            "DATABASE_URL"
        )

        if not db_url:
            raise ValueError(
                "DATABASE_URL environment variable is not set."
            )


        retries = 3


        for attempt in range(retries):

            try:

                cls._pool = pool.SimpleConnectionPool(
                    minconn,
                    maxconn,
                    db_url
                )


                logging.info(
                    f"Database connection pool initialized "
                    f"(min={minconn}, max={maxconn})"
                )

                return


            except Exception as e:

                logging.error(
                    f"Pool initialization failed "
                    f"(attempt {attempt + 1}/{retries}): {e}"
                )


                if attempt == retries - 1:
                    raise


                time.sleep(3)



    @classmethod
    def health_check(cls, conn):
        """
        Verify database connection is alive.
        """

        try:

            with conn.cursor() as cur:

                cur.execute(
                    "SELECT 1"
                )

                cur.fetchone()


            return True


        except Exception:

            return False



    @classmethod
    @contextmanager
    def get_connection(cls):
        """
        Safely provide a pooled database connection.

        Automatically:
        - initializes pool
        - validates connection
        - commits successful transactions
        - rolls back failures
        - returns connection to pool
        """

        if cls._pool is None:
            cls.initialize()


        conn = None


        try:

            conn = cls._pool.getconn()


            if not cls.health_check(conn):

                logging.warning(
                    "Invalid database connection detected. Replacing."
                )


                cls._pool.putconn(
                    conn,
                    close=True
                )


                conn = cls._pool.getconn()


            yield conn


            conn.commit()



        except Exception as e:

            if conn:

                try:

                    conn.rollback()

                except Exception:

                    pass


            logging.error(
                f"Database transaction failed: {e}"
            )

            raise



        finally:

            if conn:

                cls._pool.putconn(
                    conn
                )



    @classmethod
    def close_all(cls):
        """
        Close all pooled connections.
        """

        if cls._pool:

            cls._pool.closeall()

            cls._pool = None


            logging.info(
                "Database connection pool closed."
            )



def execute_query(
    query,
    params=None,
    fetch=True
):
    """
    Execute SQL through centralized pool.

    Returns:
        list of rows when fetch=True
        None when fetch=False
    """

    with DatabasePool.get_connection() as conn:

        with conn.cursor() as cur:

            cur.execute(
                query,
                params
            )


            if fetch:

                try:

                    return cur.fetchall()


                except psycopg2.ProgrammingError:

                    return []


            return None



def fetch_dataframe(
    query,
    params=None
):
    """
    Execute query and return pandas DataFrame.

    Use this instead of pandas.read_sql()
    with pooled psycopg2 connections.
    """

    import pandas as pd


    with DatabasePool.get_connection() as conn:

        with conn.cursor() as cur:

            cur.execute(
                query,
                params
            )


            rows = cur.fetchall()


            columns = [
                column[0]
                for column in cur.description
            ]


    return pd.DataFrame(
        rows,
        columns=columns
    )