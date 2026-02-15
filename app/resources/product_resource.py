from flask_restful import Resource
from flask import request
from bson.objectid import ObjectId
from app.db import db
from app.services.logger_service import logger
from app.models.product_model import ProductModel
from app.models.store_model import StoreModel
from app.models.product_price_model import ProductPriceModel


class ProductResource(Resource):
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
            data = request.get_json()

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
