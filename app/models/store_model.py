from app.db import db
from bson import ObjectId
from pymongo import ReturnDocument

class StoreModel:
    def __init__(self, collection):
        self.collection = collection

    def get_or_create(self, store_data: dict):
        """
        Ensures a store exists. If not, inserts it.
        Returns the _id of the matched or inserted store.
        """
        store_name = store_data.get("store")
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
