
import os
from flask import Flask
from flask_restful import Api
from .resources.product_resource import ProductResource
from .resources.product_price_resource import ProductPriceListResource
from .resources.store_resource import StoreResource
from .resources.store_search_resource import StoreSearchResource
from .services.logger_service import logger



def create_app_internal(flask_env):
    app = Flask(__name__)
    logger.info(f"Starting app in {flask_env} environment.")

    api = Api(app)

    # - map http routes to resources
    api.add_resource(ProductResource, "/products", "/products/<string:product_id>")
    api.add_resource(StoreResource, "/stores")
    api.add_resource(StoreSearchResource, "/stores/search")
    api.add_resource(ProductPriceListResource, "/products/<string:product_id>/prices")

    return app

def create_app(flask_env):
    if os.environ.get("FLASK_ENV") == "development" and os.environ.get("ENABLE_MEMORY_PROFILING") == "true":
        from memory_profiler import profile
        logger.info("Memory profiling enabled for create_app.")
        return profile(create_app_internal)(flask_env)
    else:
        return create_app_internal(flask_env)
