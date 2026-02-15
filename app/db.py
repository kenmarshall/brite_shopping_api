from pymongo import MongoClient
import os


# Load MongoDB URI and database name from environment variables
# Use `or` to handle empty strings from render.yaml placeholders
MONGO_URI = os.getenv("MONGO_URI") or "mongodb://localhost:27017/brite_shopping"
MONGO_DATABASE_NAME = os.getenv("MONGO_DATABASE_NAME") or "brite_shopping"

# Initialize the MongoDB client as a module-level singleton
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client[MONGO_DATABASE_NAME]