import googlemaps
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

class GoogleMapsService:
    def __init__(self):
        # Initialize the Google Maps client with the API key
        api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        if api_key == "mock_google_maps_key_for_testing_purposes_only":
            self.gmaps = None
        else:
            self.gmaps = googlemaps.Client(key=api_key)

    def find_store_by_address(self, address):
        """
        Finds a store location using the Google Maps API by address.
        :param address: The address of the store to search for.
        :return: A dictionary containing place_id, latitude, longitude, and formatted address.
        """
        if not self.gmaps:
            # Mock response or raise an error if testing requires this method
            raise ConnectionError("Google Maps client not initialized due to mock API key.")
        try:
            # Use the Geocoding API to find the location
            geocode_result = self.gmaps.geocode(address)
            if not geocode_result:
                raise ValueError(f"No location found for address: {address}")

            # Extract relevant data
            location = geocode_result[0]["geometry"]["location"]
            formatted_address = geocode_result[0]["formatted_address"]
            place_id = geocode_result[0]["place_id"]

            return {
                "place_id": place_id,
                "latitude": location["lat"],
                "longitude": location["lng"],
                "address": formatted_address
            }
        except Exception as e:
            raise ValueError(f"Error finding store by address: {e}")

    def find_store_by_name(self, name, location=None, radius=5000):
        """
        Finds up to 10 store locations using the Google Maps Places API by name.
        :param name: The name of the store to search for.
        :param location: Optional latitude and longitude tuple to narrow the search.
        :param radius: Search radius in meters (default: 5000).
        :return: A list of dictionaries containing name, place_id, latitude, longitude, and formatted address.
        """
        if not self.gmaps:
            # Mock response or raise an error if testing requires this method
            raise ConnectionError("Google Maps client not initialized due to mock API key.")
        try:
            # Use the Places API to find the store by name
            places_result = self.gmaps.places(name, location=location, radius=radius)
            if not places_result["results"]:
                raise ValueError(f"No store found with name: {name}")

            # Extract the top 10 results
            top_results = []
            for place in places_result["results"][:10]:
                location = place["geometry"]["location"]
                top_results.append({
                    "name": place["name"],
                    "place_id": place["place_id"],
                    "latitude": location["lat"],
                    "longitude": location["lng"],
                    "address": place.get("formatted_address", "Address not available")
                })

            return top_results
        except Exception as e:
            raise ValueError(f"Error finding store by name: {e}")
        
google_maps_service = GoogleMapsService()