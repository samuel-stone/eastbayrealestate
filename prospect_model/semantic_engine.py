import sqlite3
import pandas as pd

def run_semantic_engine():
    # Connect to your database
    conn = sqlite3.connect('scraper/output/leads.sqlite3')
    
    # Load all raw descriptions from the new table
    print("Loading permit details for semantic analysis...")
    df = pd.read_sql("SELECT * FROM permit_details", conn)
    
    # Define Intent Logic
    def get_intent(desc):
        d = str(desc).lower()
        if any(x in d for x in ['adu', 'guest house', 'addition', 'new construction']): return 'Expansion'
        if any(x in d for x in ['hvac', 'solar', 'electrical', 'plumbing', 'repipe']): return 'Systems'
        if any(x in d for x in ['kitchen', 'bath', 'remodel', 'interior']): return 'Renovation'
        return 'General'

    print("Categorizing intent...")
    df['intent_category'] = df['description'].apply(get_intent)
    
    # Save insights back to DB
    df.to_sql('permit_insights', conn, if_exists='replace', index=False)
    print("Semantic Engine: Categorized all permits into 'permit_insights' table.")
    conn.close()

if __name__ == "__main__":
    run_semantic_engine()
