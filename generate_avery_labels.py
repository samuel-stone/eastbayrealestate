import os
import pandas as pd

def generate_mailing_labels():
    csv_file = "hybrid_geometric_genai_leads.csv"
    if not os.path.exists(csv_file):
        print(f"[-] {csv_file} not found.")
        return

    df = pd.read_csv(csv_file)
    
    labels_df = pd.DataFrame()
    labels_df['Label_Name'] = "Current Resident / Property Owner"
    labels_df['Property_Address'] = df['address']
    labels_df['City_State_Zip'] = df['city'].apply(lambda x: f"{x}, CA 94595" if "ROSSMOOR" in str(x).upper() else f"{x}, CA 94596")
    labels_df['Route_Rank'] = df['geometric_route_rank']
    labels_df['Campaign_Tag'] = "Rossmoor_PreListing_Equity_Advisory"
    labels_df['Permit_Momentum'] = df['building_permit_count_24m'].astype(str) + " Permits (" + df['major_project_type'] + ")"

    output_csv = "rossmoor_avery_mailing_labels.csv"
    labels_df.to_csv(output_csv, index=False)
    print(f"[+] Successfully generated '{output_csv}' with {len(labels_df)} ready-to-print direct mail labels!")

if __name__ == "__main__":
    generate_mailing_labels()
