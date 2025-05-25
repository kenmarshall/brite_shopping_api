from flask_restful import Resource
from flask import request
from app.services.logger import logger
from app.services.google_maps import location_service

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