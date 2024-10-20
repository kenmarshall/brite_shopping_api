import configparser
import os
from flask import Flask
from flask_restful import Api
from .resources.product_resource import ProductResource
from .resources.receipt_resource import ReceiptResource
from .models.product import ProductModel
from .db import init_db
from .celery_config import init_celery

config = configparser.ConfigParser()
config.read(os.path.abspath(os.path.join("config.ini")))

def create_app(flask_env):
    app = Flask(__name__)

   # db = init_db(config, flask_env)
    
    celery = init_celery(app, config, flask_env)

    # - setup model with mongodb collections
   ## product_model = ProductModel(db.products)

    api = Api(app)

    # - map http routes to resources
    ##api.add_resource(ProductResource, "/products", "/products/<string:product_id>", resource_class_args=(product_model,))
    api.add_resource(ReceiptResource, "/receipts")

    return app, celery
