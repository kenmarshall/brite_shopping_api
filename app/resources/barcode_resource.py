from flask import request
from flask_restful import Resource
from bson.objectid import ObjectId

from app.db import db
from app.services.logger_service import logger
from app.services.store_visibility import get_hidden_store_ids


def _serialize_product(product: dict, hidden_stores: set | None = None) -> dict:
    """Minimal serialization for barcode lookup responses."""
    if not product:
        return product
    if isinstance(product.get("_id"), ObjectId):
        product["_id"] = str(product["_id"])
    product.pop("embedding", None)
    product.pop("checksum", None)
    product.pop("aliases", None)
    for key in ("created_at", "updated_at"):
        if key in product and hasattr(product[key], "isoformat"):
            product[key] = product[key].isoformat()
    if hidden_stores and "location_prices" in product:
        product["location_prices"] = [
            lp for lp in product["location_prices"]
            if lp.get("location_id") not in hidden_stores
        ]
    return product


class BarcodeResource(Resource):
    def get(self, barcode):
        """Look up a barcode. Returns the linked product if found."""
        try:
            mapping = db.barcode_mappings.find_one({"barcode": barcode})
            if not mapping:
                return {"found": False}, 404

            product_id = mapping.get("product_id")
            product = db.products.find_one({"_id": ObjectId(product_id)}) if product_id else None
            if not product:
                return {"found": False}, 404

            hidden = get_hidden_store_ids()
            return {
                "found": True,
                "product": _serialize_product(product, hidden),
            }, 200
        except Exception as e:
            logger.error(f"Barcode lookup error for {barcode}: {e}")
            return {"message": "An error occurred"}, 500

    def post(self, barcode):
        """Link a barcode to an existing product (crowdsourced mapping)."""
        try:
            data = request.get_json() or {}
            product_id = data.get("product_id", "").strip()
            if not product_id:
                return {"message": "product_id is required"}, 400

            # Validate product exists
            product = db.products.find_one({"_id": ObjectId(product_id)})
            if not product:
                return {"message": "Product not found"}, 404

            from datetime import datetime, timezone

            db.barcode_mappings.update_one(
                {"barcode": barcode},
                {
                    "$set": {
                        "barcode": barcode,
                        "product_id": product_id,
                        "source": "user_scan",
                        "product_name": product.get("name"),
                        "created_at": datetime.now(timezone.utc),
                    }
                },
                upsert=True,
            )

            return {
                "message": "Barcode linked",
                "barcode": barcode,
                "product_id": product_id,
            }, 201
        except Exception as e:
            logger.error(f"Barcode link error for {barcode}: {e}")
            return {"message": "An error occurred"}, 500

    def delete(self, barcode):
        """Unlink a barcode (remove the mapping)."""
        try:
            result = db.barcode_mappings.delete_one({"barcode": barcode})
            if result.deleted_count == 0:
                return {"message": "Barcode mapping not found"}, 404
            return {"message": "Barcode unlinked", "barcode": barcode}, 200
        except Exception as e:
            logger.error(f"Barcode unlink error for {barcode}: {e}")
            return {"message": "An error occurred"}, 500
