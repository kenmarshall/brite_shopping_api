"""
ProductModel: methods for interacting with the 'products' collection in MongoDB.
"""

import hashlib
import re
from datetime import datetime, timezone
from typing import Optional
from app.db import db
from bson.objectid import ObjectId
from app.services.logger_service import logger
from app.services.store_visibility import get_hidden_store_ids

_text_index_ready = False
_MEASURE_UNITS = r"ml|l|litre|liter|g|kg|oz|fl\s*oz|lb|lbs|gal|gallon|gallons|pt|pint|pints|qt|quart|quarts|cl|mg"
_COUNT_UNITS = r"packs?|pk|ct|count"
_SIZE_PATTERN = re.compile(
    r"(?P<value>\d+(?:\.\d+)?)\s*(?P<unit>ml|l|litre|liter|g|kg|oz|fl\s*oz|lb|lbs|gal|gallon|gallons|pt|pint|pints|qt|quart|quarts|cl|mg|pk|pack|packs|ct|count)",
    re.IGNORECASE,
)
_MULTIPACK_PATTERN = re.compile(
    rf"\b(?P<count>\d+)\s*[xX]\s*(?P<value>\d+(?:\.\d+)?)\s*(?P<unit>{_MEASURE_UNITS})\b",
    re.IGNORECASE,
)
_PACK_COUNT_PATTERN = re.compile(
    rf"\b(?:pack\s*of\s*(?P<count_a>\d+)|(?P<count_b>\d+)\s*(?:{_COUNT_UNITS}))\b",
    re.IGNORECASE,
)


def _clean_optional_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


def _normalize_name(name: str) -> str:
    lowered = str(name).lower()
    lowered = re.sub(r"[^a-z0-9\s]", " ", lowered)
    return re.sub(r"\s+", " ", lowered).strip()


def _normalize_unit(unit: str) -> str:
    compact = unit.lower().replace(" ", "")
    mapping = {
        "litre": "l",
        "liter": "l",
        "floz": "oz",
        "lbs": "lb",
        "packs": "pack",
        "pk": "pack",
        "count": "ct",
        "gallon": "gal",
        "gallons": "gal",
        "pint": "pt",
        "pints": "pt",
        "quart": "qt",
        "quarts": "qt",
    }
    return mapping.get(compact, compact)


def _parse_size(text: Optional[str]) -> dict:
    if not text:
        return {"value": None, "unit": None, "pack_count": None}

    # Check for multipack pattern first (e.g. "6x330ml", "10 x 20g")
    multipack_match = _MULTIPACK_PATTERN.search(text)
    if multipack_match:
        try:
            count = int(multipack_match.group("count"))
        except Exception:
            count = None
        try:
            value = float(multipack_match.group("value"))
        except Exception:
            value = None
        unit = _normalize_unit(multipack_match.group("unit"))
        return {"value": value, "unit": unit, "pack_count": count}

    # Check for pack count phrases (e.g. "pack of 6", "12pk")
    pack_count = None
    pack_match = _PACK_COUNT_PATTERN.search(text)
    if pack_match:
        count_raw = pack_match.group("count_a") or pack_match.group("count_b")
        if count_raw:
            try:
                pack_count = int(count_raw)
            except Exception:
                pass

    # Standard size pattern
    match = _SIZE_PATTERN.search(text)
    if not match:
        if pack_count is not None:
            return {"value": None, "unit": None, "pack_count": pack_count}
        return {"value": None, "unit": None, "pack_count": None}
    try:
        value = float(match.group("value"))
    except Exception:
        value = None
    unit = _normalize_unit(match.group("unit"))
    return {"value": value, "unit": unit, "pack_count": pack_count}


def _build_match_key(normalized_name: str, brand: Optional[str], size: dict) -> str:
    payload = (
        f"{normalized_name}|{brand or ''}|{size.get('value') or ''}|"
        f"{size.get('unit') or ''}|{size.get('pack_count') or ''}"
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _build_checksum(
    store_id: str,
    normalized_name: str,
    brand: Optional[str],
    size: dict,
) -> str:
    payload = (
        f"{store_id}|{normalized_name}|{brand or ''}|{size.get('value') or ''}|"
        f"{size.get('unit') or ''}|{size.get('pack_count') or ''}"
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


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


def _serialize(product: dict, hidden_stores: set | None = None) -> dict:
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
    # Filter out hidden store prices
    if hidden_stores and "location_prices" in product:
        product["location_prices"] = [
            lp for lp in product["location_prices"]
            if lp.get("location_id") not in hidden_stores
        ]
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
    def upsert_manual_entry(
        *,
        name: str,
        store_id: str,
        store_name: Optional[str],
        price: float,
        currency: str = "JMD",
        brand: Optional[str] = None,
        category: Optional[str] = None,
        url: Optional[str] = None,
        image_url: Optional[str] = None,
        size_hint: Optional[str] = None,
    ) -> tuple[ObjectId, bool]:
        normalized_name = _normalize_name(name)
        normalized_brand = _clean_optional_text(brand)
        normalized_category = _clean_optional_text(category)
        normalized_store_name = _clean_optional_text(store_name) or store_id
        normalized_url = _clean_optional_text(url) or f"manual://{store_id}"
        normalized_image_url = _clean_optional_text(image_url)
        normalized_currency = (currency or "JMD").strip().upper()
        parsed_size = _parse_size(size_hint or name)
        match_key = _build_match_key(normalized_name, normalized_brand, parsed_size)
        checksum = _build_checksum(store_id, normalized_name, normalized_brand, parsed_size)
        now = datetime.now(timezone.utc)

        location_price = {
            "location_id": store_id,
            "store_name": normalized_store_name,
            "amount": float(price),
            "currency": normalized_currency,
            "last_seen_at": now,
        }

        existing = db.products.find_one({"match_key": match_key})
        if existing is None:
            fallback_query = {"normalized_name": normalized_name}
            if normalized_brand:
                fallback_query["brand"] = {"$in": [normalized_brand, None, ""]}
            existing = db.products.find_one(fallback_query)

        if existing:
            location_prices = existing.get("location_prices") or []
            updated_existing_location = False
            for index, current in enumerate(location_prices):
                if current.get("location_id") == store_id:
                    location_prices[index] = location_price
                    updated_existing_location = True
                    break
            if not updated_existing_location:
                location_prices.append(location_price)

            amounts: list[float] = []
            for item in location_prices:
                amount = item.get("amount")
                try:
                    amounts.append(float(amount))
                except Exception:
                    continue
            estimated_price = round(sum(amounts) / len(amounts), 2) if amounts else None

            updates = {
                "location_prices": location_prices,
                "estimated_price": estimated_price,
                "updated_at": now,
            }

            if normalized_brand and not existing.get("brand"):
                updates["brand"] = normalized_brand
            if normalized_category and not existing.get("category"):
                updates["category"] = normalized_category
            if normalized_image_url and not existing.get("image_url"):
                updates["image_url"] = normalized_image_url
            existing_url = existing.get("url")
            if normalized_url and (not existing_url or str(existing_url).startswith("manual://")):
                updates["url"] = normalized_url
            if not existing.get("checksum"):
                updates["checksum"] = checksum
            if not existing.get("match_key"):
                updates["match_key"] = match_key
            if normalized_category:
                tags = existing.get("tags") or []
                category_tag = normalized_category.lower()
                if category_tag not in tags:
                    tags.append(category_tag)
                    updates["tags"] = tags

            db.products.update_one({"_id": existing["_id"]}, {"$set": updates})
            return existing["_id"], False

        payload = {
            "store_id": store_id,
            "store_name": normalized_store_name,
            "location_prices": [location_price],
            "estimated_price": float(price),
            "name": name.strip(),
            "normalized_name": normalized_name,
            "brand": normalized_brand,
            "size": parsed_size,
            "category": normalized_category,
            "tags": [normalized_category.lower()] if normalized_category else [],
            "aliases": [],
            "url": normalized_url,
            "image_url": normalized_image_url,
            "embedding": None,
            "created_at": now,
            "updated_at": now,
            "checksum": checksum,
            "match_key": match_key,
        }
        result = db.products.insert_one(payload)
        return result.inserted_id, True

    @staticmethod
    def get_one(product_id: str) -> Optional[dict]:
        product = db.products.find_one({"_id": ObjectId(product_id)})
        return _serialize(product, get_hidden_store_ids()) if product else None

    @staticmethod
    def find_by_name(query_name: str, limit: int = 50) -> list:
        """
        Search products by name with relevance ranking.
        1. Try MongoDB $text search (uses textScore for ranking)
        2. Fall back to regex if text search returns nothing
        """
        hidden = get_hidden_store_ids()
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
                    _serialize(product, hidden)
                return results
        except Exception as e:
            logger.warning(f"Text search failed, falling back to regex: {e}")

        # Fallback: regex search (no relevance ranking, but handles partial matches)
        regex_pattern = {"$regex": query_name, "$options": "i"}
        products = list(db.products.find({"name": regex_pattern}).limit(limit))
        for product in products:
            _serialize(product, hidden)
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
        hidden = get_hidden_store_ids()

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
                        _serialize(product, hidden)
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
                    _serialize(product, hidden)
                return results
            except Exception as e:
                logger.warning(f"Regex search failed: {e}")
                return []

        # No text query — just apply filters
        try:
            cursor = db.products.find(extra) if extra else db.products.find({})
            results = list(cursor.sort("updated_at", -1).limit(limit))
            for product in results:
                _serialize(product, hidden)
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
        hidden = get_hidden_store_ids()
        products = list(
            db.products.find({})
            .sort("updated_at", -1)
            .limit(limit)
        )
        for product in products:
            _serialize(product, hidden)
        return products
