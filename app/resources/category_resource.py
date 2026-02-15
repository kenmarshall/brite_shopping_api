from flask_restful import Resource
from app.models.product_model import ProductModel
from app.services.logger_service import logger


class CategoryResource(Resource):
    def get(self):
        try:
            return ProductModel.get_categories(), 200
        except Exception as e:
            logger.error(f"Error fetching categories: {e}")
            return {"message": "An error occurred"}, 500
