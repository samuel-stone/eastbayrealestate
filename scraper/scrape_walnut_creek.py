from config.config import Registry

# Get your list of cities
config = Registry.load_sources()
cities = config['cities']

# Get your allowed features for data validation
features = Registry.load_features()
allowed = [f['name'] for f in features['allowed_features']]

print(f"Pipeline ready. Loading targets for: {', '.join(cities)}")

# Connection string for your Aiven PostgreSQL instance
# Changed: Now pulled from environment variables for security
DB_URL = os.getenv("DATABASE_URL")
if not DB_URL:
    raise ValueError("DATABASE_URL environment variable is not set!")