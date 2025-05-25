from app.db import db  # Import the database connection
from bson import ObjectId  # Import ObjectId for MongoDB document IDs
from pymongo import ReturnDocument  # Import ReturnDocument for returning updated documents

class StoreModel:
    """
    A model class for interacting with the 'stores' collection in the database.
    Provides methods to ensure a store exists or create it if it doesn't.
    """

    def __init__(self, collection):
        """
        Initializes the StoreModel with a specific MongoDB collection.
        :param collection: The MongoDB collection to interact with.
        """
        self.collection = collection

    def get_or_create(self, store_data: dict):
        """
        Ensures a store exists in the database. If the store does not exist, it inserts it.
        Returns the _id of the matched or newly inserted store.

        :param store_data: A dictionary containing store details (e.g., name, location).
        :return: The _id of the matched or inserted store.
        :raises ValueError: If the store name is not provided in the input data.
        """
        # Extract the store name from the input data
        store_name = store_data.get("store")
        
        # Raise an error if the store name is missing
        if not store_name:
            raise ValueError("Store name is required")

        # Remove None values from the store_data to avoid inserting empty fields
        clean_data = {k: v for k, v in store_data.items() if v is not None}

        store = self.collection.find_one_and_update(
            {"store": store_name},                  # Match by name
            {"$setOnInsert": clean_data},           # Only insert if new
            upsert=True,
            return_document=ReturnDocument.AFTER
        )

        return store["_id"]

    def get(self, store_id):
        store = self.collection.find_one({"_id": ObjectId(store_id)})
        if store:
            store["_id"] = str(store["_id"])
        return store

    def get_all(self):
        stores = list(self.collection.find())
        for store in stores:
            store["_id"] = str(store["_id"])
        return stores

store_model = StoreModel(db.stores)
