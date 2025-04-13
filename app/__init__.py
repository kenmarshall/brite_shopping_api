import configparser
import os

from .services.logger import setup_logger
from flask import Flask
from flask_restful import Api
from .resources.product_resource import ProductResource
from .resources.receipt_resource import ReceiptResource
from .models.product import ProductModel
from .db import init_db
from .celery_config import init_celery

config = configparser.ConfigParser()
config.read(os.path.abspath(os.path.join("config.ini")))

logger = None
product_model = None
def create_app(flask_env):
  global logger, product_model
  app = Flask(__name__)

  db = init_db(config, flask_env)
    
  # celery = init_celery(app, config, flask_env)
  
  # Initialize the logger
  logger = setup_logger()
  logger.info("Logger initialized successfully.")

  # Example: Log the environment
  logger.info(f"Starting app in {flask_env} environment.")
  # - setup model with mongodb collections
  product_model = ProductModel(db.products)

  api = Api(app)

    # - map http routes to resources
  api.add_resource(ProductResource, "/products", "/products/<string:product_id>")
  api.add_resource(ReceiptResource, "/receipts")

  return app
