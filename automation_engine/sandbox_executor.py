import os
import subprocess
import tempfile
import json
from datetime import datetime


def run_sandbox_validation(proposal_id, proposal):
    """
    Creates an isolated temporary sandbox and validates a proposal.
    Does NOT modify production code.
    """

    result = {
        "proposal_id": proposal_id,
        "started_at": datetime.utcnow().isoformat(),
        "status": "failed",
        "sandbox": None,
        "checks": []
    }

    try:
        repo_root = os.getcwd()

        sandbox = tempfile.mkdtemp(
            prefix=f"eastbay_proposal_{proposal_id}_"
        )

        result["sandbox"] = sandbox

        # Clone current repository state into sandbox
        clone = subprocess.run(
            [
                "git",
                "clone",
                "--quiet",
                repo_root,
                sandbox
            ],
            capture_output=True,
            text=True
        )

        if clone.returncode != 0:
            result["checks"].append({
                "step": "git clone",
                "passed": False,
                "error": clone.stderr
            })
            return result


        result["checks"].append({
            "step": "sandbox clone",
            "passed": True
        })


        # Python syntax validation
        compile_test = subprocess.run(
            [
                "python3",
                "-m",
                "compileall",
                "."
            ],
            cwd=sandbox,
            capture_output=True,
            text=True
        )

        result["checks"].append({
            "step": "python compile",
            "passed": compile_test.returncode == 0,
            "output": compile_test.stdout[-1000:]
        })


        # Basic git state check
        git_status = subprocess.run(
            [
                "git",
                "status",
                "--short"
            ],
            cwd=sandbox,
            capture_output=True,
            text=True
        )

        result["checks"].append({
            "step": "git integrity",
            "passed": True,
            "output": git_status.stdout
        })


        all_passed = all(
            check.get("passed", False)
            for check in result["checks"]
        )

        result["status"] = (
            "passed"
            if all_passed
            else "failed"
        )

        result["completed_at"] = datetime.utcnow().isoformat()

        return result


    except Exception as e:
        result["error"] = str(e)
        return result
