from bson import ObjectId
from datetime import datetime, timezone
from app.db import db
from pymongo import ReturnDocument # Added import


class ProductPriceModel:
    @staticmethod
    def upsert_price(product_id: str, store_id: str, price: float, currency: str = "JMD"):
        """
        Updates an existing price entry for a product at a specific store,
        or inserts a new price entry if one does not already exist.

        :param product_id: The ID of the product.
        :param store_id: The ID of the store.
        :param price: The price of the product.
        :param currency: The currency of the price (defaults to "JMD").
        :return: The _id of the updated or newly inserted price document.
        """
        # Convert string IDs to ObjectId
        obj_product_id = ObjectId(product_id)
        obj_store_id = ObjectId(store_id)

        query = {
            "product_id": obj_product_id,
            "store_id": obj_store_id
        }

        update_payload = {
            "$set": {
                "price": price,
                "currency": currency,
                "last_updated": datetime.now(timezone.utc)
            },
            # If the document is created (upserted), we also need to ensure
            # product_id and store_id are set. $setOnInsert is good for this.
            "$setOnInsert": {
                "product_id": obj_product_id,
                "store_id": obj_store_id
            }
        }

        # Using find_one_and_update with upsert=True handles both cases:
        # - If a document matching the query exists, it's updated according to $set.
        # - If no document matches, a new one is inserted using fields from $set and $setOnInsert.
        result_doc = db.product_prices.find_one_and_update(
            query,
            update_payload,
            upsert=True,
            return_document=ReturnDocument.AFTER # Return the document after update/insert
        )

        return result_doc["_id"]

    @staticmethod
    def get_prices_for_product(product_id):
        """
        Returns a list of prices for a given product, enriched with store details.
        """
        pipeline = [
            {"$match": {"product_id": ObjectId(product_id)}},
            {
                "$lookup": {
                    "from": "stores",
                    "localField": "store_id",
                    "foreignField": "_id",
                    "as": "store"
                }
            },
            {"$unwind": "$store"},
            {"$sort": {"price": 1}}
        ]
        prices = list(db.product_prices.aggregate(pipeline))

        # Convert ObjectId fields to string for client response
        for price in prices:
            price["_id"] = str(price["_id"])
            price["product_id"] = str(price["product_id"])
            price["store_id"] = str(price["store_id"])
            price["store"]["_id"] = str(price["store"]["_id"])

        return prices

    @staticmethod
    def get_lowest_price(product_id):
        """
        Returns the store and price info for the lowest available price.
        """
        pipeline = [
            {"$match": {"product_id": ObjectId(product_id)}},
            {
                "$lookup": {
                    "from": "stores",
                    "localField": "store_id",
                    "foreignField": "_id",
                    "as": "store"
                }
            },
            {"$unwind": "$store"},
            {"$sort": {"price": 1}},
            {"$limit": 1}
        ]
        result = list(db.product_prices.aggregate(pipeline))
        if not result:
            return None

        item = result[0]
        item["_id"] = str(item["_id"])
        item["product_id"] = str(item["product_id"])
        item["store_id"] = str(item["store_id"])
        item["store"]["_id"] = str(item["store"]["_id"])
        return item
