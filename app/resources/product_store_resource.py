from flask_restful import Resource

from app.db import db
from app.services.logger_service import logger


class ProductStoreResource(Resource):
    def get(self):
        """Return distinct store_id/store_name pairs from products with counts."""
        try:
            pipeline = [
                {"$match": {"store_id": {"$ne": None}}},
                {
                    "$group": {
                        "_id": "$store_id",
                        "store_name": {"$first": "$store_name"},
                        "product_count": {"$sum": 1},
                    }
                },
                {"$sort": {"product_count": -1}},
                {
                    "$project": {
                        "_id": 0,
                        "store_id": "$_id",
                        "store_name": 1,
                        "product_count": 1,
                    }
                },
            ]
            results = list(db.products.aggregate(pipeline))
            return results, 200
        except Exception as e:
            logger.error(f"Error fetching product stores: {e}")
            return {"message": "An error occurred"}, 500
