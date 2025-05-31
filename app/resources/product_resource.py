from flask_restful import Resource
from flask import request
from app.services.logger_service import logger
from app.models.product_model import ProductModel
from app.models.store_model import store_model
from app.models.product_price_model import product_price_model


class ProductResource(Resource):
    def get(self, product_id=None):
        try:
            # Find by the product id
            if product_id:
                return ProductModel.get_one(product_id), 200
            # Find by name
            name = request.args.get("name")

            if name:
                products = ProductModel.find_by_name(name)
                return products, 200

            # All products - to include pagination or some explore/filtering options
            return ProductModel.get_all(), 200
        except Exception as e:
            logger.error(f"Error occurred while fetching product(s): {e}")
            return {"message": "An error occurred"}, 500

    # Expects JSON: {"product_data": {...}, "store_info": {"place_id": ..., ...}, "price": ..., "currency": ...}
    def post(self):
        try:
            data = request.get_json()

            product_data = data.get("product_data")
            store_info = data.get("store_info")
            price = data.get("price")
            currency = data.get("currency", "JMD")  # Default currency if not provided

            # Basic validation
            if not product_data or not product_data.get("name"):
                return {"message": "Product data with name is required"}, 400
            if not store_info:
                return {"message": "Store info is required"}, 400
            if not store_info.get("place_id"):
                return {"message": "Store place_id is required"}, 400
            if price is None or not isinstance(price, (int, float)):
                return {"message": "Price is required and must be a number"}, 400

            # Get or create store
            store_id = store_model.get_or_create(store_info)

            # Add product
            product_id = ProductModel.add_product(product_data)

            # Add product price
            product_price_model.add_price(product_id, store_id, price, currency)

            return {
                "message": "Product created successfully",
                "product_id": str(product_id),
                "store_id": str(store_id)
            }, 201
        except ValueError as ve:
            logger.error(f"Validation error while adding a new product: {ve}")
            return {"message": str(ve)}, 400
        except Exception as e:
            logger.error(f"Error occurred while adding a new product: {e}")
            return {"message": "An error occurred"}, 500

    def put(self, product_id):
        data = request.get_json()
        # self.product_model.update_one({"_id": product_id}, data)
        return {"status": "success"}, 200

    def delete(self, product_id):
        # mongo.db.products.delete_one({"_id": product_id})
        return {"status": "success"}, 200
