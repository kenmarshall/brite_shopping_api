"""
ProductModel: methods for interacting with the 'products' collection in MongoDB.
"""

from typing import Optional
from app.db import db
from bson.objectid import ObjectId
from app.services.logger_service import logger

_text_index_ready = False


def _ensure_text_index():
    """Create a compound text index for relevance-ranked search if it doesn't exist."""
    global _text_index_ready
    if _text_index_ready:
        return

    try:
        existing = db.products.index_information()
        _expected_fields = {"name", "normalized_name", "brand", "category", "tags"}

        # Drop any existing text index that doesn't match our current schema
        for idx_name, idx_info in existing.items():
            if idx_name == "search_text":
                # Verify the index has all expected fields
                weights = idx_info.get("weights", {})
                if set(weights.keys()) == _expected_fields:
                    _text_index_ready = True
                    return
                # Index schema changed — drop and recreate
                logger.info("Text index schema changed, recreating...")
                db.products.drop_index(idx_name)
                break
            # Check if it's a text index we need to replace
            if any(v == "text" for _, v in idx_info.get("key", [])):
                logger.info(f"Dropping existing text index: {idx_name}")
                db.products.drop_index(idx_name)

        db.products.create_index(
            [
                ("name", "text"),
                ("normalized_name", "text"),
                ("brand", "text"),
                ("category", "text"),
                ("tags", "text"),
            ],
            name="search_text",
            weights={"name": 10, "normalized_name": 8, "brand": 5, "category": 4, "tags": 3},
        )
        logger.info("Created text search index on products collection")
        _text_index_ready = True
    except Exception as e:
        logger.warning(f"Could not create text index: {e}")


def _serialize(product: dict) -> dict:
    """Make a product document JSON-serializable."""
    if not product:
        return product
    if isinstance(product.get("_id"), ObjectId):
        product["_id"] = str(product["_id"])
    # Drop embedding vector (768 floats, not needed by clients)
    product.pop("embedding", None)
    product.pop("checksum", None)
    product.pop("aliases", None)
    # Convert datetimes to ISO strings
    for key in ("created_at", "updated_at"):
        if key in product and hasattr(product[key], "isoformat"):
            product[key] = product[key].isoformat()
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
    def _build_extra_filters(category: str = None, tag: str = None, store_id: str = None) -> dict:
        """Build MongoDB filter clauses for category/tag/store_id."""
        f = {}
        if category:
            f["category"] = {"$regex": category, "$options": "i"}
        if tag:
            f["tags"] = {"$regex": tag, "$options": "i"}
        if store_id:
            f["store_id"] = store_id
        return f

    @staticmethod
    def search(query: str = None, category: str = None, tag: str = None, store_id: str = None, limit: int = 50) -> list:
        """
        Forgiving search with two-pass strategy:
        1. Try MongoDB $text search for full-word relevance ranking
        2. Fall back to regex prefix matching across name, brand, category, and tags
        This ensures partial queries like "maca" match "Macaroni".
        """
        extra = ProductModel._build_extra_filters(category, tag, store_id)

        # Pass 1: full-text search (works for complete words, ranked by relevance)
        if query:
            try:
                _ensure_text_index()
                text_filter = {"$text": {"$search": query}, **extra}
                projection = {"score": {"$meta": "textScore"}}
                results = list(
                    db.products.find(text_filter, projection)
                    .sort([("score", {"$meta": "textScore"})])
                    .limit(limit)
                )
                if results:
                    for product in results:
                        product.pop("score", None)
                        _serialize(product)
                    return results
            except Exception as e:
                logger.warning(f"Text search failed, trying regex: {e}")

        # Pass 2: regex prefix search (handles partial words, typos-ish)
        if query:
            import re
            escaped = re.escape(query)
            regex = {"$regex": escaped, "$options": "i"}
            regex_filter = {
                "$or": [
                    {"name": regex},
                    {"normalized_name": regex},
                    {"brand": regex},
                    {"category": regex},
                    {"tags": regex},
                ],
                **extra,
            }
            try:
                results = list(
                    db.products.find(regex_filter)
                    .sort("updated_at", -1)
                    .limit(limit)
                )
                for product in results:
                    _serialize(product)
                return results
            except Exception as e:
                logger.warning(f"Regex search failed: {e}")
                return []

        # No text query — just apply filters
        try:
            cursor = db.products.find(extra) if extra else db.products.find({})
            results = list(cursor.sort("updated_at", -1).limit(limit))
            for product in results:
                _serialize(product)
            return results
        except Exception as e:
            logger.warning(f"Search failed: {e}")
            return []

    @staticmethod
    def get_categories(limit: int = 20) -> list:
        """Return top categories ranked by product count.

        Splits comma-separated category values so each individual
        category is counted independently (e.g. "Baby & Infant,Medicine"
        contributes one count to each).
        """
        try:
            pipeline = [
                {"$match": {"category": {"$ne": None, "$ne": ""}}},
                # Split comma-separated categories into individual values
                {"$project": {"cats": {"$split": ["$category", ","]}}},
                {"$unwind": "$cats"},
                {"$project": {"cat": {"$trim": {"input": "$cats"}}}},
                {"$match": {"cat": {"$ne": ""}}},
                {"$group": {"_id": "$cat", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": limit},
            ]
            results = list(db.products.aggregate(pipeline))
            return [r["_id"] for r in results]
        except Exception as e:
            logger.warning(f"Failed to get categories: {e}")
            return []

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
