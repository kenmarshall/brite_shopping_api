from flask import Flask
from flask_restful import Api
from .resources import HelloWorld, ReceiptUpload, Product
import configparser
import os
from .db import mongo

config = configparser.ConfigParser()
config.read(os.path.abspath(os.path.join("config.ini")))


def create_app():
    app = Flask(__name__)
    app.config["MONGO_URI"] = config["DEV"]["MONGO_URI"]

    mongo.init_app(app)
    
    print(mongo.db.products.insert_one( {"price": 1.99, "name": "test"}))  

    api = Api(app)
    api.add_resource(HelloWorld, "/")
    api.add_resource(ReceiptUpload, "/receipt")
    api.add_resource(Product, "/product")

    return app
