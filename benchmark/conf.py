import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

RESULTS_LIMIT = 30
RESULTS_DIR = os.path.join(BASE_DIR, "results")

DATABASE_PATH = os.path.join(BASE_DIR, "database.json")
SCHEMA_PATH = os.path.join(BASE_DIR, "schema.graphql")
