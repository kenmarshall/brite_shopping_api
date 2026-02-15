from pymongo import MongoClient
import certifi
import os


# Load MongoDB URI and database name from environment variables
# Use `or` to handle empty strings from render.yaml placeholders
MONGO_URI = os.getenv("MONGO_URI") or "mongodb://localhost:27017/brite_shopping"
MONGO_DATABASE_NAME = os.getenv("MONGO_DATABASE_NAME") or "brite_shopping"

# Initialize the MongoDB client as a module-level singleton
# tlsCAFile=certifi.where() fixes SSL handshake errors on Render/cloud hosts
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000, tlsCAFile=certifi.where())
db = client[MONGO_DATABASE_NAME]