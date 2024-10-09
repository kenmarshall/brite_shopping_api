from flask import request
from flask_restful import Resource
from .db import mongo


class HelloWorld(Resource):
    def get(self):
        return {'hello': 'world'}
      
class ReceiptUpload(Resource):
    def post(self):
        file = request.files['file']


   
        