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
        place_id = store_data.get("place_id")
        if not place_id:
            raise ValueError("Store place_id is required")

        # Validate that store name is provided and not empty
        if store_data.get("store") is None:
            raise ValueError("Store name ('store' field) is required and cannot be empty.")

        # Prepare data for $set: filter out None values, and exclude place_id from this dict
        # as place_id is the query key and is handled by $setOnInsert for new documents.
        data_for_set = {
            k: v for k, v in store_data.items() if k != "place_id" and v is not None
        }
        # Ensure that the 'store' (name) field, if originally provided and not None, is in data_for_set.
        # This check is implicitly handled by store_data.get("store") is None above and the dict comprehension.
        # If store_data.get("store") was valid, it will be in data_for_set.

        store = db.stores.find_one_and_update(
            {"place_id": place_id},  # Query by place_id
            {
                # $set applies these fields if the document is found, or sets them on creation.
                # It will update existing fields or add new ones from store_data.
                "$set": data_for_set,
                # $setOnInsert ensures place_id is written only when a new document is created.
                "$setOnInsert": {"place_id": place_id}
            },
            upsert=True,  # Create the document if it doesn't exist
            return_document=ReturnDocument.AFTER  # Return the modified or new document
        )
        return store["_id"]  # Return the ObjectId of the store

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
