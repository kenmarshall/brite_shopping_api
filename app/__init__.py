
import os
from flask import Flask
from flask_restful import Api
from memory_profiler import profile
from .resources.product_resource import ProductResource
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

    return app

def create_app(flask_env):
    if os.environ.get("FLASK_ENV") == "development" and os.environ.get("ENABLE_MEMORY_PROFILING") == "true":
        # Apply the profile decorator only in development and when ENABLE_MEMORY_PROFILING is true
        logger.info("Memory profiling enabled for create_app.")
        return profile(create_app_internal)(flask_env)
    else:
        # In other environments, call the original function directly
        return create_app_internal(flask_env)
