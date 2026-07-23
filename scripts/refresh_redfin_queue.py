import os
import psycopg2

conn = psycopg2.connect(os.environ["DATABASE_URL"])
cur = conn.cursor()

cur.execute("""
INSERT INTO redfin_scrape_queue(id,address,url)
SELECT
    id,
    address,
    'https://www.redfin.com/search?q=' ||
    replace(address || ' ' || city,' ','%20')
FROM leads
WHERE property_id IS NULL
AND city IS NOT NULL
ON CONFLICT(id) DO NOTHING;
""")

conn.commit()

print("queue refreshed")
