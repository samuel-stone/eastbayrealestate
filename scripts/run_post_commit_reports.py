import os
import sys

ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

sys.path.insert(0, ROOT)

from automation_engine.code_reviewer import review_commit


if __name__ == "__main__":

    print("[+] Triggering automated AI code review...")

    review_commit()

    print("[+] Automated AI review completed successfully.")
