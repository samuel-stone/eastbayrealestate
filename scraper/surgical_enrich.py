import pandas as pd
import os

def generate_html_links():
    # Ensure the input file exists
    if not os.path.exists('adu_prospect_list.csv'):
        print("[Error] 'adu_prospect_list.csv' not found. Ensure it is in the current directory.")
        return

    df = pd.read_csv('adu_prospect_list.csv')
    
    with open('clickable_leads.html', 'w') as f:
        f.write("<html><body><h1>Property Research List</h1><ul>")
        for _, row in df.iterrows():
            address = row['address']
            # Redfin lookup URL
            search_query = address.replace(" ", "+")
            url = f"https://www.redfin.com/stingray/do/lookup-location?location={search_query}"
            f.write(f'<li><a href="{url}" target="_blank">{address}</a></li>')
        f.write("</ul></body></html>")
    
    print("[Status] 'clickable_leads.html' created successfully.")

if __name__ == "__main__":
    generate_html_links()