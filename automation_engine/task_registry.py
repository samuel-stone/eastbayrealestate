import importlib

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

def run_task(job):
    """Dynamically loads and executes a task by its registered module path."""
    task_name = job["name"]
    module_path = get_task_module(task_name)
    
    if not module_path:
        raise ValueError(f"Task '{task_name}' is not found in TASK_REGISTRY.")
    
    print(f"Loading module: {module_path}")
    module = importlib.import_module(module_path)
    
    # Execute the module's main() function
    if hasattr(module, 'main'):
        module.main()
    else:
        raise AttributeError(f"Module '{module_path}' is missing a main() function to execute.")