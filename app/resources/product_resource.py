from flask_restful import Resource
from flask import request
from bson.objectid import ObjectId
from app.db import db
from app.services.logger_service import logger
from app.models.product_model import ProductModel
from app.models.store_model import StoreModel
from app.models.product_price_model import ProductPriceModel


class ProductResource(Resource):
    @staticmethod
    def _validate_manual_payload(data):
        name = str(data.get("name", "")).strip()
        store_id = str(data.get("store_id", "")).strip().lower() or None
        store_name = str(data.get("store_name", "")).strip() or store_id
        brand = str(data.get("brand", "")).strip() or None
        category = str(data.get("category", "")).strip() or None
        currency = str(data.get("currency", "JMD")).strip().upper() or "JMD"
        size_hint = str(data.get("size_hint", "")).strip() or None
        image_url = str(data.get("image_url", "")).strip() or None
        url = str(data.get("url", "")).strip() or None
        place_id = str(data.get("place_id", "")).strip() or None

        if len(name) < 2:
            return None, {"message": "Product name must be at least 2 characters"}, 400

        price = None
        if store_id:
            raw_price = data.get("price")
            try:
                price = float(raw_price)
            except (TypeError, ValueError):
                return None, {"message": "price is required when store is provided"}, 400
            if price <= 0:
                return None, {"message": "price must be greater than 0"}, 400
            if len(currency) != 3:
                return None, {"message": "currency must be a 3-letter code"}, 400
        elif data.get("price") is not None:
            try:
                price = float(data.get("price"))
            except (TypeError, ValueError):
                pass

        payload = {
            "name": name,
            "store_id": store_id,
            "store_name": store_name,
            "price": price,
            "currency": currency,
            "brand": brand,
            "category": category,
            "size_hint": size_hint,
            "image_url": image_url,
            "url": url,
            "place_id": place_id,
            "latitude": data.get("latitude"),
            "longitude": data.get("longitude"),
            "address": str(data.get("address", "")).strip() or None,
        }
        return payload, None, None

    def get(self, product_id=None):
        try:
            # Find by the product id
            if product_id:
                return ProductModel.get_one(product_id), 200

            # Check for any search/filter params
            query = request.args.get("q") or request.args.get("name")
            category = request.args.get("category")
            tag = request.args.get("tag")
            store_id = request.args.get("store_id")
            limit = request.args.get("limit", 50, type=int)

            if query or category or tag or store_id:
                products = ProductModel.search(
                    query=query,
                    category=category,
                    tag=tag,
                    store_id=store_id,
                    limit=limit,
                )
                return products, 200

            # No filters — return recent products
            return ProductModel.get_all(limit=limit), 200
        except Exception as e:
            logger.error(f"Error occurred while fetching product(s): {e}")
            return {"message": "An error occurred", "error": str(e)}, 500

    # Expects JSON: {"product_data": {...}, "store_info": {"place_id": ..., ...}, "price": ..., "currency": ...}
    def post(self):
        try:
            data = request.get_json() or {}

            # New mobile/manual flow:
            # {"name": "...", "store_id": "hilo", "store_name": "...", "price": 120.0, ...}
            # Keep legacy flow below for backwards compatibility.
            if "product_data" not in data and "store_info" not in data:
                payload, error_body, error_code = self._validate_manual_payload(data)
                if error_body:
                    return error_body, error_code

                # Save Google Places store data if provided
                if payload.get("place_id"):
                    db.stores.update_one(
                        {"place_id": payload["place_id"]},
                        {"$set": {
                            "place_id": payload["place_id"],
                            "store_name": payload.get("store_name"),
                            "latitude": payload.get("latitude"),
                            "longitude": payload.get("longitude"),
                            "address": payload.get("address"),
                        }},
                        upsert=True,
                    )

                # Strip non-model fields before passing to upsert
                model_fields = {k: v for k, v in payload.items()
                                if k not in ("place_id", "latitude", "longitude", "address")}

                if model_fields.get("store_id") and model_fields.get("price"):
                    product_id, created = ProductModel.upsert_manual_entry(**model_fields)
                    return {
                        "message": "Product created" if created else "Product updated",
                        "product_id": str(product_id),
                        "store_id": model_fields["store_id"],
                    }, 201 if created else 200

                # No store — product-only creation
                from datetime import datetime, timezone
                now = datetime.now(timezone.utc)
                name = model_fields["name"]
                brand = model_fields.get("brand")
                category = model_fields.get("category")
                image_url = model_fields.get("image_url")

                # Check for existing product by normalized name
                normalized = name.strip().lower()
                existing = db.products.find_one({"normalized_name": normalized})
                if existing:
                    updates = {"updated_at": now}
                    if brand and not existing.get("brand"):
                        updates["brand"] = brand
                    if category and not existing.get("category"):
                        updates["category"] = category
                    if image_url and not existing.get("image_url"):
                        updates["image_url"] = image_url
                    db.products.update_one({"_id": existing["_id"]}, {"$set": updates})
                    return {
                        "message": "Product already exists",
                        "product_id": str(existing["_id"]),
                    }, 200

                product_doc = {
                    "name": name,
                    "normalized_name": normalized,
                    "brand": brand,
                    "category": category,
                    "size": None,
                    "tags": [category.lower()] if category else [],
                    "aliases": [],
                    "location_prices": [],
                    "estimated_price": None,
                    "image_url": image_url,
                    "url": model_fields.get("url"),
                    "embedding": None,
                    "created_at": now,
                    "updated_at": now,
                }
                result = db.products.insert_one(product_doc)
                return {
                    "message": "Product created",
                    "product_id": str(result.inserted_id),
                }, 201

            product_data = data.get("product_data")
            store_info = data.get("store_info")
            price = data.get("price")
            currency = data.get("currency", "JMD")

            if not product_data or not product_data.get("name"):
                return {"message": "Product data with name is required"}, 400
            if not store_info:
                return {"message": "Store info is required"}, 400
            if not store_info.get("place_id"): # Assuming store_info contains place_id
                return {"message": "Store place_id is required"}, 400
            if price is None or not isinstance(price, (int, float)): # Check type of price
                return {"message": "Price is required and must be a number"}, 400

            # Get or create store
            store_id = StoreModel.get_or_create(store_info)

            # Get or create product
            product_id = ProductModel.get_or_create_product(product_data)

            # Add or update product price
            # Ensure product_id and store_id are strings when passed to upsert_price
            price_id = ProductPriceModel.upsert_price(str(product_id), str(store_id), price, currency)

            return {
                "message": "Product information processed successfully",
                "product_id": str(product_id),
                "store_id": str(store_id),
                "price_id": str(price_id)
            }, 201
        except ValueError as ve:
            logger.error(f"Validation error while processing product information: {ve}")
            return {"message": str(ve)}, 400
        except Exception as e:
            logger.error(f"Error occurred while processing product information: {e}")
            return {"message": "An error occurred"}, 500

    def put(self, product_id):
        try:
            data = request.get_json()
            if not data:
                return {"message": "Request body is required"}, 400

            result = db.products.update_one(
                {"_id": ObjectId(product_id)},
                {"$set": data}
            )

            if result.matched_count == 0:
                return {"message": "Product not found"}, 404

            return {"message": "Product updated", "product_id": product_id}, 200
        except Exception as e:
            logger.error(f"Error updating product {product_id}: {e}")
            return {"message": "An error occurred"}, 500

    def delete(self, product_id):
        try:
            result = db.products.delete_one({"_id": ObjectId(product_id)})

            if result.deleted_count == 0:
                return {"message": "Product not found"}, 404

            return {"message": "Product deleted", "product_id": product_id}, 200
        except Exception as e:
            logger.error(f"Error deleting product {product_id}: {e}")
            return {"message": "An error occurred"}, 500
