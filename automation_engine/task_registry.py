import importlib
import traceback
import time
from datetime import datetime



TASK_REGISTRY = {


    "redfin_scrape":
        "scraper.scrape_redfin:main",


    "redfin_enrich":
        "scraper.enrich_redfin:main",


    "scrape_redfin":
    [

        "scraper.scrape_redfin:main",

        "scraper.enrich_redfin:main"

    ],


    "process_leads":
        "automation_engine.tasks.process_leads:main",


    "enrich_properties":
        "automation_engine.tasks.enrich_properties:main",


    "hybrid_ai_enrichment":
        "automation_engine.tasks.hybrid_ai_enrichment:main",


    "local_ai_analysis":
        "local_ai_agent:main"

}




def execute_task(path):

    started=time.time()


    module_name, function_name = path.split(":")


    result={

        "task":path,

        "success":False,

        "started_at":
            datetime.utcnow().isoformat(),

        "duration":None

    }


    try:


        module=importlib.import_module(
            module_name
        )


        func=getattr(
            module,
            function_name
        )


        output=func()


        result.update({

            "success":True,

            "output":str(output)

        })


    except Exception as e:


        result.update({

            "error":
                str(e),

            "traceback":
                traceback.format_exc()

        })


    finally:


        result["duration"]=round(
            time.time()-started,
            3
        )


    return result





def run_task(job):


    task=job["name"]


    entry=TASK_REGISTRY.get(
        task
    )


    if not entry:


        return {

            "success":False,

            "error":
                f"Unknown task {task}"

        }



    steps=[]


    if isinstance(
        entry,
        list
    ):

        for step in entry:

            result=execute_task(step)

            steps.append(result)


            if not result["success"]:

                return {

                    "success":False,

                    "task":task,

                    "steps":steps,

                    "error":
                        result.get(
                            "error"
                        )

                }



    else:


        steps.append(
            execute_task(entry)
        )


        if not steps[0]["success"]:

            return {

                "success":False,

                "task":task,

                "steps":steps,

                "error":
                    steps[0].get(
                        "error"
                    )

            }



    return {

        "success":True,

        "task":task,

        "steps":steps

    }