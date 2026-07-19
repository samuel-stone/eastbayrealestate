import json
import os
import keyring

class Registry:
    # Use 'config' as the base path since this file lives in /config/
    BASE_PATH = os.path.dirname(os.path.abspath(__file__))

    @staticmethod
    def get_db_url():
        password = keyring.get_password("eastbay-db-password", os.environ.get("USER"))
        return f"postgres://avnadmin:{password}@pg-305dd876-eastbayrealestate.l.aivencloud.com:22742/defaultdb"

    @classmethod
    def load_sources(cls):
        with open(os.path.join(cls.BASE_PATH, 'sources.json'), 'r') as f:
            return json.load(f)

    @classmethod
    def load_features(cls):
        with open(os.path.join(cls.BASE_PATH, 'feature_registry.json'), 'r') as f:
            return json.load(f)