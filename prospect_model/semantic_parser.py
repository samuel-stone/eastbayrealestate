import sqlite3
import pandas as pd

def classify_description(desc):
    if not isinstance(desc, str): return 'General'
    desc = desc.lower()
    # Expand your categories here
    intent_map = {
        'Expansion': ['adu', 'addition', 'guest house'],
        'Systems': ['hvac', 'electrical', 'solar', 'plumbing'],
        'Renovation': ['kitchen', 'bathroom', 'remodel']
    }
    for category, keywords in intent_map.items():
        if any(kw in desc for kw in keywords):
            return category
    return 'General'

def enrich_database():
    conn = sqlite3.connect('scraper/output/leads.sqlite3')
    
    # Query using the tables you confirmed exist
    query = """
        SELECT l.id, f.description 
        FROM leads l
        JOIN prospect_features f ON l.id = f.lead_id
    """
    df = pd.read_sql_query(query, conn)
    
    df['intent_category'] = df['description'].apply(classify_description)
    df.to_sql('permit_intent_scores', conn, if_exists='replace', index=False)
    
    print("Enrichment complete. Table 'permit_intent_scores' created.")
    conn.close()

if __name__ == "__main__":
    enrich_database()
