
from flask import Flask
from flask_restful import Api
from .resources.product_resource import ProductResource
from .resources.receipt_resource import ReceiptResource
from .services.logger import logger

# from .celery_config import init_celery


def create_app(flask_env):
    app = Flask(__name__)
    logger.info(f"Starting app in {flask_env} environment.")

    api = Api(app)

    # - map http routes to resources
    api.add_resource(ProductResource, "/products", "/products/<string:product_id>")
    api.add_resource(ReceiptResource, "/receipts")

    return app
