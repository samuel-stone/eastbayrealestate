import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# This loads your DATABASE_URL from your .env file automatically
load_dotenv()

db_url = os.environ.get("DATABASE_URL")
if not db_url:
    print("Error: DATABASE_URL not found in environment or .env file.")
    exit(1)

# FIX: SQLAlchemy requires 'postgresql://' but Railway often provides 'postgres://'
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

engine = create_engine(db_url)

print("Connecting to database to create sandbox tables...")
with engine.connect() as conn:
    # Create the sandbox tables
    conn.execute(text("CREATE TABLE IF NOT EXISTS scraped_property_data_sandbox AS SELECT * FROM scraped_property_data WHERE 1=0;"))
    conn.execute(text("CREATE TABLE IF NOT EXISTS leads_sandbox AS SELECT * FROM leads WHERE 1=0;"))
    conn.commit()
    
print("Success! Sandbox tables created safely.")