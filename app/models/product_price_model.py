from bson import ObjectId
from datetime import datetime, timezone
from app.db import db


class ProductPriceModel:
    @staticmethod
    def add_price(product_id, store_id, price, currency="JMD"):
        """
        Adds a price entry linking a product and a store.
        """
        price_doc = {
            "product_id": ObjectId(product_id),
            "store_id": ObjectId(store_id),
            "price": price,
            "currency": currency,
            "last_updated": datetime.now(timezone.utc)
        }
        db.product_prices.insert_one(price_doc)

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
