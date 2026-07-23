from . import process_leads
from . import enrich_properties
from . import hybrid_ai_enrichment

TASKS = {
    'process_leads': process_leads.main,
    'enrich_properties': enrich_properties.main,
    'hybrid_ai_enrichment': hybrid_ai_enrichment.main,
}

def main():

    print(
        "Hybrid AI enrichment task started"
    )

    return None