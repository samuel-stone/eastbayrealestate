# Task Registry mapping task names to their respective python modules
TASK_REGISTRY = {
    "scrape_redfin": "scraper.scrape_redfin",
    "discover_listings": "scraper.discover_listings",
    "process_leads": "automation_engine.tasks.process_leads",
    "enrich_properties": "automation_engine.tasks.enrich_properties",
    "hybrid_ai_enrichment": "automation_engine.tasks.hybrid_ai_enrichment",
    "local_ai_analysis": "local_ai_agent"
}

def get_task_module(task_name):
    return TASK_REGISTRY.get(task_name)
