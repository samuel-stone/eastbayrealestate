DROP VIEW IF EXISTS redfin_scrape_queue;

CREATE TABLE IF NOT EXISTS redfin_scrape_queue (
    id INTEGER PRIMARY KEY REFERENCES leads(id) ON DELETE CASCADE,
    address TEXT,
    url TEXT,
    status TEXT DEFAULT 'queued',
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    last_error TEXT
);


INSERT INTO redfin_scrape_queue (
    id,
    address,
    url
)
SELECT
    id,
    address,
    'https://www.redfin.com/search?q=' ||
    replace(address || ' ' || city, ' ', '%20')
FROM leads
WHERE property_id IS NULL
AND city IS NOT NULL
ON CONFLICT (id) DO NOTHING;


CREATE INDEX IF NOT EXISTS idx_redfin_queue_status
ON redfin_scrape_queue(status);
