import re

file_path = 'prospect_model/batch_load_permits.py'
with open(file_path, 'r') as f:
    content = f.read()

# This looks for your current UPDATE pattern and inserts the INSERT logic immediately after
pattern = r'(cursor\.execute\("""\s*UPDATE prospect_features.*?\)\)'
replacement = r'\1\n    cursor.execute("""\n        INSERT INTO permit_details (lead_id, description, permit_type, date_processed)\n        VALUES (?, ?, ?, ?)\n    """, (lead_id, permit_desc, permit_type, datetime.now().isoformat()))'

if re.search(pattern, content, re.DOTALL):
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    with open(file_path, 'w') as f:
        f.write(new_content)
    print("Successfully patched prospect_model/batch_load_permits.py to include semantic logging.")
else:
    print("Could not find the update pattern. You may need to manual edit.")
