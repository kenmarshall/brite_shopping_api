from flask_restful import Resource
from flask import request, jsonify
from app import logger


# TODO: Add error handling and logging
class ProductResource(Resource):
    def __init__(self, product_model):
        self.product_model = product_model

    def get(self, product_id=None):
        try:
            if product_id:
                product = self.product_model.get_one(product_id)
                return product, 200
            products = self.product_model.get_all()
            return products, 200
        except Exception as e:
            logger.error(f"Error occurred while fetching product(s): {e}")
            return {"message": "An error occurred"}, 500

    def post(self):
        try:
            data = request.get_json()
            self.product_model.add(data)
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
