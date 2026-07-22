import subprocess
import json
from datetime import datetime

from automation_engine.ai_client import ask_ollama
from automation_engine.agent_memory import remember


def run_git(command):
    return subprocess.check_output(
        command,
        text=True
    ).strip()


def get_commit_context():

    commit = run_git([
        "git",
        "rev-parse",
        "--short",
        "HEAD"
    ])

    message = run_git([
        "git",
        "log",
        "-1",
        "--pretty=%B"
    ])

    files = run_git([
        "git",
        "show",
        "--name-only",
        "--format=",
        "HEAD"
    ])

    diff = run_git([
        "git",
        "show",
        "--format=",
        "--patch",
        "HEAD"
    ])

    return {
        "commit": commit,
        "message": message,
        "files": files,
        "diff": diff
    }


def review_commit():

    ctx = get_commit_context()

    prompt = f"""
You are a senior software engineer performing a production code review.

Repository:
East Bay Real Estate AI Automation Platform

Commit:
{ctx['commit']}

Commit Message:
{ctx['message']}

Changed Files:
{ctx['files']}


Review ONLY the supplied git diff.

IMPORTANT RULES:
- Do not invent bugs.
- Do not assume code exists that is not shown.
- Do not criticize unchanged code.
- Only report issues proven by the diff.
- If no real issue exists, say "No critical issues found."


Analyze:

1. Real bugs introduced
2. Database risks
3. Security problems
4. Async/concurrency issues
5. Performance regressions
6. Missing tests
7. Architecture concerns


Return:

severity:
file:
problem:
evidence from diff:
recommendation:


DIFF:

{ctx['diff']}
"""

    review = ask_ollama(prompt)


    analysis_prompt = f"""
You are a software review classifier.

Analyze this review:

{review}

Return ONLY valid JSON.

Schema:

{{
  "severity": "Low|Medium|High|Critical",
  "confidence": integer 0-100,
  "recommended_action": "ignore|human_review|auto_fix_candidate"
}}

Rules:
- Confidence reflects how strongly the issue is proven.
- Speculative issues should have low confidence.
- Real reproducible bugs should have high confidence.
"""


    classification = ask_ollama(analysis_prompt)


    try:
        classification_data = json.loads(classification)

    except Exception:
        classification_data = {
            "severity": "Unknown",
            "confidence": 0,
            "recommended_action": "human_review"
        }


    observation = {
        "type": "code_review",
        "commit": ctx["commit"],
        "message": ctx["message"],
        "files": ctx["files"].splitlines(),

        "severity": classification_data.get(
            "severity",
            "Unknown"
        ),

        "confidence": classification_data.get(
            "confidence",
            0
        ),

        "recommended_action": classification_data.get(
            "recommended_action",
            "human_review"
        ),

        "review": review,

        "created": str(datetime.now())
    }


    remember(
        json.dumps(observation)
    )


    print("=" * 60)
    print("AI CODE REVIEW")
    print("=" * 60)

    print(
        f"Severity: {classification_data.get('severity')}"
    )

    print(
        f"Confidence: {classification_data.get('confidence')}%"
    )

    print(
        f"Recommended Action: {classification_data.get('recommended_action')}"
    )

    print()

    print(review)


if __name__ == "__main__":
    review_commit()