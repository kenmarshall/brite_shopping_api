from flask import request
from flask_restful import Resource
from app.services.google_maps_service import google_maps_service # Assuming this is the instance
from app.services.logger_service import logger

class StoreSearchResource(Resource):
    def get(self):
        query_name = request.args.get("name")
        query_address = request.args.get("address")

        if not query_name and not query_address:
            return {"message": "A 'name' or 'address' query parameter is required"}, 400

        try:
            results = []
            if query_name:
                # TODO: Consider allowing UI to pass location bias (lat,lng) and radius
                results = google_maps_service.find_store_by_name(name=query_name)
            elif query_address:
                # find_store_by_address currently returns a single dict or raises error
                # To make return type consistent with find_store_by_name (list of results),
                # we wrap the single result in a list.
                store_details = google_maps_service.find_store_by_address(address=query_address)
                if store_details:
                    results = [store_details]

            # Normalization: Ensure all results have a 'name' field if possible
            # find_store_by_address doesn't return 'name' directly from geocode,
            # but find_store_by_name does. This might need UI handling or further lookup.
            # For now, we keep them as returned by the service.

            return {"stores": results}, 200

        except ValueError as ve:
            # ValueError from services (e.g., "No location found", "Invalid API key")
            logger.warning(f"Store search failed for query_name='{query_name}', query_address='{query_address}': {str(ve)}")
            # Return specific message, could be 404 if "not found" or 400 for bad input.
            # Let's use 400 for client errors (bad/missing query) and 404 if service says "not found".
            # The current google_maps_service raises ValueError for "No store found".
            if "No location found" in str(ve) or "No store found" in str(ve):
                 return {"message": str(ve), "stores": []}, 404
            return {"message": f"Search parameter error: {str(ve)}"}, 400
        except Exception as e:
            logger.error(f"An unexpected error occurred during store search for query_name='{query_name}', query_address='{query_address}': {e}")
            return {"message": "An internal server error occurred"}, 500
