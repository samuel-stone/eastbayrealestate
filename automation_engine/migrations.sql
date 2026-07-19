CREATE TABLE IF NOT EXISTS scheduled_jobs (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    job_type TEXT NOT NULL,
    interval_minutes INTEGER NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    last_run TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO scheduled_jobs
(name, job_type, interval_minutes)
VALUES
('Daily Market Report','daily_market_report',1440),
('Listing Scraper','scrape_listings',60)
ON CONFLICT DO NOTHING;
