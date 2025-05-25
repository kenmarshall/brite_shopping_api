from flask_restful import Resource
from flask import request

from app.models.store_model import StoreModel
from app.services.logger_service import logger
from app.services.google_maps_service import location_service

class StoreResource(Resource):
    def get(self):
        """
        Handles GET requests to find store by address or name.
        :return: JSON response containing store data.
        """
        try:
            # Check if the request is for finding a store by address or name
            if "address" in request.args:
                address = request.args.get("address")
                logger.info(f"Finding store by address: {address}")
                result = location_service.find_store_by_address(address)
            elif "name" in request.args:
                name = request.args.get("name")
                location = request.args.get("location")
                radius = request.args.get("radius", default=5000, type=int)
                logger.info(f"Finding store by name: {name}, location: {location}, radius: {radius}")
                result = location_service.find_store_by_name(name, location, radius)
            else:
                return {"error": "Please provide either an address or a name."}, 400

            return {"data": result}, 200
        except Exception as e:
            logger.error(f"Error finding store location: {e}")
            return {"error": str(e)}, 500

    def post(self):
        """
        Handles POST requests to create or retrieve a store.
        :return: JSON response containing store ID and status code.
        """
        try:
            data = request.get_json()
            if not data or "name" not in data:
                logger.error("Store name is required.")
                return {"error": "Store name is required."}, 400

            store_name = data["name"]
            # Assuming address is optional for now, add if required by get_or_create
            # address = data.get("address") 

            store, created = StoreModel.get_or_create(name=store_name)
            
            if created:
                logger.info(f"Store '{store_name}' created with ID: {store.id}")
                return {"id": store.id, "message": "Store created."}, 201
            else:
                logger.info(f"Store '{store_name}' already exists with ID: {store.id}")
                return {"id": store.id, "message": "Store already exists."}, 200
        except Exception as e:
            logger.error(f"Error creating or retrieving store: {e}")
            return {"error": str(e)}, 500