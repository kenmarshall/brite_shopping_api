from flask_restful import Resource
from flask import request
from app.services.logger import logger
from app.models.product_model import product_model


class ProductResource(Resource):
    def get(self, product_id=None):
        try:
            # Find by the product id
            if product_id:
                return product_model.get_one(product_id), 200
            # Find by name
            name = request.args.get("name")

            if name:
                products = product_model.find_by_name(name)
                return products, 200

            # All products - to include pagination or some explore/filtering options
            return product_model.get_all(), 200
        except Exception as e:
            logger.error(f"Error occurred while fetching product(s): {e}")
            return {"message": "An error occurred"}, 500

    def post(self):
        try:
            data = request.get_json()
            product_model.add(data)
            return {"status": "success"}, 201
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
