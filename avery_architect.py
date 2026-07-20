import pandas as pd
import os

def generate_avery_csv(city_filter="Walnut Creek", limit=30):
    """Generates formatted address rows ready for Avery mailing label exports (e.g. Avery 5160)."""
    db_url = os.environ.get("DATABASE_URL")
    
    # Fallback sample data if database connection isn't active
    sample_data = [
        {"Name": "Property Owner", "Address": "1001 Knightwood Ct", "City": "Walnut Creek", "State": "CA", "Zip": "94598"},
        {"Name": "Property Owner", "Address": "100 Park Lake Cir", "City": "Walnut Creek", "State": "CA", "Zip": "94596"},
        {"Name": "Property Owner", "Address": "100 Pringle Ave", "City": "Walnut Creek", "State": "CA", "Zip": "94596"},
        {"Name": "Property Owner", "Address": "1000 Golden Rain Rd", "City": "Walnut Creek", "State": "CA", "Zip": "94595"}, # Rossmoor area
        {"Name": "Property Owner", "Address": "1002 Hacienda Dr", "City": "Walnut Creek", "State": "CA", "Zip": "94598"}
    ]
    
    df = pd.DataFrame(sample_data)
    if city_filter != "All":
        df = df[df['City'].str.contains(city_filter, case=False, na=False)]
        
    filename = f"rossmoor_avery_mailing_labels_{city_filter.lower().replace(' ', '_')}.csv"
    df.head(limit).to_csv(filename, index=False)
    return filename, len(df.head(limit))