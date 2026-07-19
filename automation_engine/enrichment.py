from datetime import datetime


def enrich_property(property_data):

    print(
        "Enriching:",
        property_data
    )


    enriched = {

        **property_data,

        "enriched_at":
            str(datetime.now()),

        "score":
            None,

        "signals":
            []

    }


    return enriched



def run_enrichment_batch(properties):

    results=[]


    for p in properties:

        results.append(
            enrich_property(p)
        )


    return results
