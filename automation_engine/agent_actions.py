from automation_engine.database import add_job, get_connection


def queue_job(name):

    job_id = add_job(name)

    print(
        "AGENT ACTION: queued",
        name,
        "job_id:",
        job_id
    )

    return job_id



def retry_failed_jobs():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id,name
        FROM jobs
        WHERE status='failed'
        """
    )

    jobs = cur.fetchall()


    for job in jobs:

        print(
            "AGENT RETRY:",
            job["name"]
        )

        cur.execute(
            """
            UPDATE jobs
            SET status='queued',
                last_error=NULL
            WHERE id=%s
            """,
            (
                job["id"],
            )
        )


    conn.commit()

    cur.close()
    conn.close()



def run_agent_actions():

    print(
        "Agent actions online"
    )

    retry_failed_jobs()