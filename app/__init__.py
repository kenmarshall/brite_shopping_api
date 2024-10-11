from flask import Flask
from flask_restful import Api
from .resources.product_resource import ProductResource
from .models.product import ProductModel
from .db import init_db


def create_app():
    app = Flask(__name__)

    db = init_db()

    # - setup model with mongodb collections
    product_model = ProductModel(db.products)

    api = Api(app)

    # - map http routes to resources
    api.add_resource(ProductResource, "/products", "/products/<string:product_id>", resource_class_args=(product_model,))

    return app
