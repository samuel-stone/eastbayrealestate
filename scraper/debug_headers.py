import requests

url = "https://www.contracosta.ca.gov/Archive.aspx?ADID=6975"
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
response = requests.get(url, headers=headers)

print(f"Status Code: {response.status_code}")
print(f"Content-Type: {response.headers.get('Content-Type')}")
print(f"File Size (bytes): {len(response.content)}")

if 'text/html' in response.headers.get('Content-Type', '').lower():
    print("\n=== RAW HTML SNIPPET (First 800 chars) ===")
    print(response.text[:800])
