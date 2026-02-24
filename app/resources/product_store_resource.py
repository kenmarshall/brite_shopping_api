from flask_restful import Resource

from app.db import db
from app.services.logger_service import logger
from app.services.store_visibility import get_hidden_store_ids


def _get_excluded_store_ids() -> set[str]:
    """Return store_ids that are hidden or not entity_type='store'."""
    excluded: set[str] = set()
    for doc in db.store_settings.find({}, {"store_id": 1, "visible": 1, "entity_type": 1}):
        sid = doc.get("store_id")
        if not sid:
            continue
        if not doc.get("visible", True):
            excluded.add(sid)
        entity_type = doc.get("entity_type", "store")
        if entity_type != "store":
            excluded.add(sid)
    return excluded


class ProductStoreResource(Resource):
    def get(self):
        """Return distinct store_id/store_name pairs from products with counts.

        Only returns sources that are entity_type='store' and not hidden.
        Aggregates product counts from location_prices[] (where scraped products
        store their store relationship).
        """
        try:
            excluded = _get_excluded_store_ids()

            # Aggregate by location_id in location_prices[] (scraped products)
            lp_pipeline: list[dict] = [
                {"$unwind": {"path": "$location_prices", "preserveNullAndEmptyArrays": False}},
            ]
            if excluded:
                lp_pipeline.append(
                    {"$match": {"location_prices.location_id": {"$nin": list(excluded)}}}
                )
            lp_pipeline += [
                {
                    "$group": {
                        "_id": "$location_prices.location_id",
                        "store_name": {"$first": "$location_prices.store_name"},
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
            results = list(db.products.aggregate(lp_pipeline))

            # Also include manually-added products (top-level store_id, empty location_prices)
            sid_filter: dict = {
                "store_id": {"$ne": None},
                "location_prices": {"$size": 0},
            }
            if excluded:
                sid_filter["store_id"]["$nin"] = list(excluded)
            sid_pipeline = [
                {"$match": sid_filter},
                {
                    "$group": {
                        "_id": "$store_id",
                        "store_name": {"$first": "$store_name"},
                        "product_count": {"$sum": 1},
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "store_id": "$_id",
                        "store_name": 1,
                        "product_count": 1,
                    }
                },
            ]
            existing_ids = {r["store_id"] for r in results}
            for row in db.products.aggregate(sid_pipeline):
                if row["store_id"] not in existing_ids:
                    results.append(row)

            results.sort(key=lambda r: r.get("product_count", 0), reverse=True)
            return results, 200
        except Exception as e:
            logger.error(f"Error fetching product stores: {e}")
            return {"message": "An error occurred"}, 500
