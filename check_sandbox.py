import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

db_url = os.environ.get("DATABASE_URL", "")
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

engine = create_engine(db_url)

print("--- leads_sandbox data ---")
with engine.connect() as conn:
    result = conn.execute(text("SELECT address, lead_rating FROM leads_sandbox;"))
    for row in result:
        print(f"Address: {row[0]} | Rating: {row[1]}")
