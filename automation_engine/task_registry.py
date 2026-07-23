import importlib
import traceback
import time
from datetime import datetime


# ============================================================
# Task Registry
# ============================================================

TASK_REGISTRY = {

    # Redfin Pipeline
    "redfin_scrape": "scraper.scrape_redfin",
    "redfin_enrich": "scraper.enrich_redfin",

    "scrape_redfin": [
        "scraper.scrape_redfin",
        "scraper.enrich_redfin"
    ],


    # Municipal Loaders
    "load_walnut_creek_permits":
        "scripts.load_walnut_creek_permits",

    "load_rossmoor_permits":
        "scripts.load_rossmoor_permits",

    "load_orinda_permits":
        "scripts.load_orinda_permits",

    "load_lafayette_permits":
        "scripts.load_lafayette_permits",

    "load_zillow_comps":
        "scripts.load_zillow_comps",


    # Core Automation Tasks
    "discover_listings":
        "scraper.discover_listings",

    "process_leads":
        "automation_engine.tasks.process_leads",

    "enrich_properties":
        "automation_engine.tasks.enrich_properties",

    "hybrid_ai_enrichment":
        "automation_engine.tasks.hybrid_ai_enrichment",

    "local_ai_analysis":
        "local_ai_agent"
}



# ============================================================
# Execute Individual Module
# ============================================================

def execute_module(module_path):
    """
    Import and execute a task module.

    Every execution returns structured telemetry.
    """

    started = time.time()

    result = {
        "module": module_path,
        "success": False,
        "started_at": datetime.utcnow().isoformat(),
        "completed_at": None,
        "duration_seconds": None,
        "error": None,
        "traceback": None,
        "retryable": True
    }


    try:

        print(
            f"[Task Registry] Loading {module_path}"
        )

        module = importlib.import_module(
            module_path
        )


        if not hasattr(module, "main"):

            raise AttributeError(
                f"{module_path} does not expose main()"
            )


        print(
            f"[Task Registry] Executing {module_path}.main()"
        )


        module.main()


        result["success"] = True
        result["retryable"] = False


    except Exception as exc:


        error_type = type(exc).__name__

        result["error"] = (
            f"{error_type}: {str(exc)}"
        )

        result["traceback"] = traceback.format_exc()


        # These usually indicate code problems,
        # not transient failures.

        if error_type in [
            "ImportError",
            "ModuleNotFoundError",
            "AttributeError",
            "SyntaxError"
        ]:
            result["retryable"] = False


        print(
            f"[Task Registry] FAILED {module_path}: "
            f"{result['error']}"
        )


        print(
            result["traceback"]
        )


    finally:

        result["duration_seconds"] = round(
            time.time() - started,
            3
        )

        result["completed_at"] = (
            datetime.utcnow().isoformat()
        )


    return result



# ============================================================
# Execute Job
# ============================================================

def run_task(job):
    """
    Execute a registered automation job.

    Input:
        {
            "id": 123,
            "name": "process_leads"
        }

    Returns:
        structured execution result
    """


    task_name = job.get(
        "name"
    )


    if not task_name:

        return {
            "success": False,
            "error": "Missing job name",
            "retryable": False
        }



    registry_entry = TASK_REGISTRY.get(
        task_name
    )


    if registry_entry is None:

        return {
            "success": False,
            "task": task_name,
            "error": "Task not registered",
            "retryable": False
        }



    results = []


    try:


        # Pipeline execution

        if isinstance(
            registry_entry,
            list
        ):


            print(
                f"[Pipeline] Starting {task_name}"
            )


            for module_path in registry_entry:


                step = execute_module(
                    module_path
                )


                results.append(step)


                if not step["success"]:

                    return {
                        "success": False,
                        "task": task_name,
                        "failed_step": module_path,
                        "steps": results,
                        "retryable": step["retryable"]
                    }



        else:


            results.append(
                execute_module(
                    registry_entry
                )
            )


        return {
            "success": True,
            "task": task_name,
            "steps": results
        }



    except Exception as exc:


        return {
            "success": False,
            "task": task_name,
            "error": str(exc),
            "traceback": traceback.format_exc(),
            "retryable": True
        }