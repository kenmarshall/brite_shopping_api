from flask_restful import Resource
from flask import request
from app.db import mongo


class ProductResource(Resource):
    def get(self, product_id):
        return mongo.db.products.find_one_or_404({"_id": product_id})
    def post(self):
        data = request.get_json()
        mongo.db.products.insert_one(data)
        return {'status': 'success'}, 201
    def put(self, product_id):
        data = request.get_json()
        mongo.db.products.update_one({"_id": product_id}, data)
        return {'status': 'success'}, 200
    def delete(self, product_id):
        mongo.db.products.delete_one({"_id": product_id})
        return {'status': 'success'}, 200