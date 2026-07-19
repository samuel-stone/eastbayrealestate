import os
from dotenv import load_dotenv
load_dotenv()
from config.config import Registry
# Connection string for your Aiven PostgreSQL instance
# Changed: Now pulled from environment variables for security
DB_URL = os.getenv("DATABASE_URL")
if not DB_URL:
    raise ValueError("DATABASE_URL environment variable is not set!")
