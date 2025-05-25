
from flask import Flask
from flask_restful import Api
from .resources.product_resource import ProductResource
from .resources.store_resource import StoreResource
from .services.logger_service import logger



def create_app(flask_env):
    app = Flask(__name__)
    logger.info(f"Starting app in {flask_env} environment.")

    api = Api(app)

    # - map http routes to resources
    api.add_resource(ProductResource, "/products", "/products/<string:product_id>")
    api.add_resource(StoreResource, "/stores")

    return app
