import importlib

# Task Registry mapping task names to their respective python modules
TASK_REGISTRY = {
    # Modular Redfin Scripts (Updated to correct 'scraper' folder)
    "redfin_scrape": "scraper.scrape_redfin",
    "redfin_parse": "scraper.parse_redfin_html",
    "redfin_enrich": "scraper.enrich_redfin",
    
    # Full Redfin Pipeline (Sequential Execution)
    "scrape_redfin": [
        "scraper.scrape_redfin",
        "scraper.parse_redfin_html",
        "scraper.enrich_redfin"
    ],
    
    # Municipal & Comps Loaders (Assuming these are actually in a scripts/ folder)
    "load_walnut_creek_permits": "scripts.load_walnut_creek_permits",
    "load_rossmoor_permits": "scripts.load_rossmoor_permits",
    "load_orinda_permits": "scripts.load_orinda_permits",
    "load_lafayette_permits": "scripts.load_lafayette_permits",
    "load_zillow_comps": "scripts.load_zillow_comps",

    # Original Legacy Tasks
    "discover_listings": "scraper.discover_listings",
    "process_leads": "automation_engine.tasks.process_leads",
    "enrich_properties": "automation_engine.tasks.enrich_properties",
    "hybrid_ai_enrichment": "automation_engine.tasks.hybrid_ai_enrichment",
    "local_ai_analysis": "local_ai_agent"
}

def execute_module(module_path):
    """Helper function to load and execute a single module."""
    print(f"Loading module: {module_path}")
    module = importlib.import_module(module_path)
    
    # Execute the module's main() function
    if hasattr(module, 'main'):
        module.main()
    else:
        raise AttributeError(f"Module '{module_path}' is missing a main() function to execute.")

def run_task(job):
    """Dynamically loads and executes a task by its registered module path."""
    task_name = job["name"]
    registry_entry = TASK_REGISTRY.get(task_name)
    
    if not registry_entry:
        raise ValueError(f"Task '{task_name}' is not found in TASK_REGISTRY.")
    
    if isinstance(registry_entry, list):
        print(f"[*] Executing pipeline job: {task_name} ({len(registry_entry)} steps)")
        for step_path in registry_entry:
            execute_module(step_path)
    else:
        execute_module(registry_entry)