"""
ProductModel: methods for interacting with the 'products' collection in MongoDB.
"""

from typing import Optional
from app.db import db
from bson.objectid import ObjectId
from app.services.logger_service import logger


def _ensure_text_index():
    """Create a compound text index for relevance-ranked search if it doesn't exist."""
    existing = db.products.index_information()
    if "search_text" not in existing:
        db.products.create_index(
            [
                ("name", "text"),
                ("normalized_name", "text"),
                ("brand", "text"),
                ("tags", "text"),
            ],
            name="search_text",
            weights={"name": 10, "normalized_name": 8, "brand": 5, "tags": 3},
        )
        logger.info("Created text search index on products collection")


# Ensure index exists on module load
try:
    _ensure_text_index()
except Exception as e:
    logger.warning(f"Could not create text index (will retry on first search): {e}")


def _serialize(product: dict) -> dict:
    """Convert ObjectId to string for JSON serialization."""
    if product and isinstance(product.get("_id"), ObjectId):
        product["_id"] = str(product["_id"])
    return product


class ProductModel:

    @staticmethod
    def get_or_create_product(data: dict) -> ObjectId:
        product_name = data.get("name")
        if not product_name:
            raise ValueError("Product name ('name' field) is required.")

        existing_product = db.products.find_one({"name": product_name})

        if existing_product:
            return existing_product["_id"]
        else:
            result = db.products.insert_one(data)
            return result.inserted_id

    @staticmethod
    def get_one(product_id: str) -> Optional[dict]:
        product = db.products.find_one({"_id": ObjectId(product_id)})
        return _serialize(product) if product else None

    @staticmethod
    def find_by_name(query_name: str, limit: int = 50) -> list:
        """
        Search products by name with relevance ranking.
        1. Try MongoDB $text search (uses textScore for ranking)
        2. Fall back to regex if text search returns nothing
        """
        # Attempt text search with relevance scoring
        try:
            _ensure_text_index()
            results = list(
                db.products.find(
                    {"$text": {"$search": query_name}},
                    {"score": {"$meta": "textScore"}},
                )
                .sort([("score", {"$meta": "textScore"})])
                .limit(limit)
            )
            if results:
                for product in results:
                    product.pop("score", None)
                    _serialize(product)
                return results
        except Exception as e:
            logger.warning(f"Text search failed, falling back to regex: {e}")

        # Fallback: regex search (no relevance ranking, but handles partial matches)
        regex_pattern = {"$regex": query_name, "$options": "i"}
        products = list(db.products.find({"name": regex_pattern}).limit(limit))
        for product in products:
            _serialize(product)
        return products

    @staticmethod
    def get_all(limit: int = 100) -> list:
        """Return products sorted by most recently updated, with a default limit."""
        products = list(
            db.products.find({})
            .sort("updated_at", -1)
            .limit(limit)
        )
        for product in products:
            _serialize(product)
        return products
