import os
import sys
import json
import psycopg2
from datetime import datetime


ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

sys.path.insert(0, ROOT)


from automation_engine.code_reviewer import review_commit

from code_architect import generate_proposals
from analytics_architect import generate_analytics_notebook


def log_to_agent_memory(title, summary):
    """
    Saves auto-generated reports into agent_memory safely.
    Uses json.dumps to prevent malformed JSON from AI-generated text.
    """

    database_url = os.environ.get("DATABASE_URL")

    if not database_url:
        print("[-] DATABASE_URL not found in environment.")
        return

    try:
        conn = psycopg2.connect(
            database_url,
            connect_timeout=10
        )

        cur = conn.cursor()

        observation = json.dumps(
            {
                "type": "post_commit_report",
                "title": title,
                "summary": summary
            },
            ensure_ascii=False
        )

        cur.execute(
            """
            INSERT INTO agent_memory
            (
                observation,
                created_at
            )
            VALUES
            (
                %s,
                %s
            )
            """,
            (
                observation,
                datetime.now()
            )
        )

        conn.commit()

        cur.close()
        conn.close()

        print(
            f"[+] Successfully logged '{title}' to database agent_memory!"
        )

    except Exception as e:
        print(
            f"[-] Failed to write report to database: {e}"
        )


if __name__ == "__main__":

    print(
        "[+] Triggering automated post-commit reporting workflow..."
    )


    # --------------------------------------------------
    # 1. Generate AI architecture proposals
    # --------------------------------------------------

    try:
        proposals, source = generate_proposals()

        log_to_agent_memory(
            f"Codebase Review ({source})",
            proposals[:1000]
        )

    except Exception as e:
        print(
            f"[-] Proposal generation failed: {e}"
        )


    # --------------------------------------------------
    # 2. Generate analytics notebook
    # --------------------------------------------------

    try:
        nb_file = generate_analytics_notebook()

        log_to_agent_memory(
            "Analytics Notebook Compilation",
            f"Successfully generated notebook file: {nb_file}"
        )

    except Exception as e:
        print(
            f"[-] Analytics generation failed: {e}"
        )


    # --------------------------------------------------
    # 3. AI Code Review
    # --------------------------------------------------

    try:
        print(
            "[+] Running AI Code Review..."
        )

        review_commit()

        print(
            "[+] Automated AI review completed successfully."
        )

    except Exception as e:
        print(
            f"[-] AI code review failed: {e}"
        )


    print(
        "[+] Automated post-commit pipeline completed successfully."
    )