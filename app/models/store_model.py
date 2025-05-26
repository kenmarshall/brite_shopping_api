from app.db import db  # Import the database connection
from bson import ObjectId  # Import ObjectId for MongoDB document IDs
from pymongo import ReturnDocument  # Import ReturnDocument for returning updated documents

class StoreModel:
    """
    A model class for interacting with the 'stores' collection in the database.
    Provides methods to ensure a store exists or create it if it doesn't.
    """

    @staticmethod
    def get_or_create(store_data: dict):
        """
        Ensures a store exists in the database. If the store does not exist, it inserts it.
        Returns the _id of the matched or newly inserted store.

        :param store_data: A dictionary containing store details (e.g., name, location).
        :return: The _id of the matched or inserted store.
        :raises ValueError: If the store name is not provided in the input data.
        """
        # Extract the store name and place_id from the input data
        store_name = store_data.get("store")
        place_id = store_data.get("place_id")

        # Raise an error if the store name is missing (can be removed later if not needed)
        if not store_name:
            raise ValueError("Store name is required")

        # Raise an error if place_id is missing
        if not place_id:
            raise ValueError("Store place_id is required")

        # Remove None values from the store_data to avoid inserting empty fields
        # Ensure place_id is part of clean_data if it exists in store_data
        clean_data = {k: v for k, v in store_data.items() if v is not None}
        if "place_id" not in clean_data and place_id:
             clean_data["place_id"] = place_id


        store = db.stores.find_one_and_update(
            {"store": store_name},                  # Match by name
            {"$setOnInsert": clean_data},           # Only insert if new
            upsert=True,
            return_document=ReturnDocument.AFTER
        )

        return store["_id"]

    @staticmethod
    def get(store_id):
        store = db.stores.find_one({"_id": ObjectId(store_id)})
        if store:
            store["_id"] = str(store["_id"])
        return store

    @staticmethod
    def get_all():
        stores = list(db.stores.find())
        for store in stores:
            store["_id"] = str(store["_id"])
        return stores
