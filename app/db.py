from pymongo import MongoClient
import os


# Load MongoDB URI and database name from environment variables
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/brite_shopping")
MONGO_DATABASE_NAME = os.getenv("MONGO_DATABASE_NAME", "brite_shopping_db")

# Initialize the MongoDB client as a module-level singleton
client = MongoClient(MONGO_URI)
db = client[MONGO_DATABASE_NAME]