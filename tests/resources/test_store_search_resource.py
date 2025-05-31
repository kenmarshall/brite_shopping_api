import pytest
from flask import Flask
from flask_restful import Api
from unittest.mock import patch, MagicMock

# Need to ensure app.services.google_maps_service.google_maps_service is mocked
# *before* StoreSearchResource tries to import it.
# One way is to patch it where it's looked up.

# Mock the GoogleMapsService instance directly in the services module
# This mock will be active when StoreSearchResource is imported.
mock_gmaps_service_instance = MagicMock()

# Option 1: If google_maps_service is imported as 'from app.services.google_maps_service import google_maps_service'
# sys.modules['app.services.google_maps_service'] = MagicMock(google_maps_service=mock_gmaps_service_instance)

# Option 2: More targeted patch using unittest.mock.patch later in the test setup.
# This is generally cleaner.

from app.resources.store_search_resource import StoreSearchResource
from app.services.logger_service import logger # StoreSearchResource uses this

# Disable logging for tests to keep output clean
logger.disabled = True

@pytest.fixture
def app_test_client():
    app = Flask(__name__)
    api = Api(app)
    # Patch 'google_maps_service' within the module where StoreSearchResource will find it.
    # This ensures that StoreSearchResource uses our mock.
    with patch('app.resources.store_search_resource.google_maps_service', mock_gmaps_service_instance):
        api.add_resource(StoreSearchResource, '/stores/search')
        client = app.test_client()
        yield client
    # Reset the mock for other tests if necessary, though fixture scope should handle it.
    mock_gmaps_service_instance.reset_mock()


def test_search_by_name_success(app_test_client):
    mock_gmaps_service_instance.find_store_by_name.return_value = [
        {"name": "Test Store", "place_id": "pid1", "address": "123 Test St"}
    ]
    response = app_test_client.get('/stores/search?name=Test')
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data["stores"] == [
        {"name": "Test Store", "place_id": "pid1", "address": "123 Test St"}
    ]
    mock_gmaps_service_instance.find_store_by_name.assert_called_once_with(name="Test")
    mock_gmaps_service_instance.find_store_by_address.assert_not_called()

def test_search_by_address_success(app_test_client):
    mock_gmaps_service_instance.find_store_by_address.return_value = {
        "place_id": "pid2", "address": "456 Main Ave"
        # Note: find_store_by_address in the resource wraps this in a list
    }
    response = app_test_client.get('/stores/search?address=456%20Main%20Ave') # URL encoded
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data["stores"] == [
        {"place_id": "pid2", "address": "456 Main Ave"}
    ]
    mock_gmaps_service_instance.find_store_by_address.assert_called_once_with(address="456 Main Ave")
    mock_gmaps_service_instance.find_store_by_name.assert_not_called()

def test_search_missing_query_param(app_test_client):
    response = app_test_client.get('/stores/search')
    assert response.status_code == 400
    json_data = response.get_json()
    assert "message" in json_data
    assert "A 'name' or 'address' query parameter is required" in json_data["message"]
    mock_gmaps_service_instance.find_store_by_name.assert_not_called()
    mock_gmaps_service_instance.find_store_by_address.assert_not_called()

def test_search_name_not_found(app_test_client):
    # Simulate "No store found" error from the service
    mock_gmaps_service_instance.find_store_by_name.side_effect = ValueError("No store found with name: NonExistent")
    response = app_test_client.get('/stores/search?name=NonExistent')
    assert response.status_code == 404 # As per StoreSearchResource logic for "No store found"
    json_data = response.get_json()
    assert "No store found" in json_data["message"]
    assert json_data["stores"] == []
    mock_gmaps_service_instance.find_store_by_name.assert_called_once_with(name="NonExistent")

def test_search_address_not_found(app_test_client):
    mock_gmaps_service_instance.find_store_by_address.side_effect = ValueError("No location found for address: NonExistent Address")
    response = app_test_client.get('/stores/search?address=NonExistent%20Address')
    assert response.status_code == 404
    json_data = response.get_json()
    assert "No location found" in json_data["message"]
    assert json_data["stores"] == []
    mock_gmaps_service_instance.find_store_by_address.assert_called_once_with(address="NonExistent Address")

def test_search_google_service_generic_value_error(app_test_client):
    # Simulate other ValueErrors like "Invalid API key" or other issues from the service
    mock_gmaps_service_instance.find_store_by_name.side_effect = ValueError("Some other Google API error")
    response = app_test_client.get('/stores/search?name=Query')
    # This should be a 400 as it's not a "not found" error but more like a bad request/config from service's perspective
    assert response.status_code == 400
    json_data = response.get_json()
    assert "Search parameter error: Some other Google API error" in json_data["message"]

def test_search_unexpected_exception(app_test_client):
    mock_gmaps_service_instance.find_store_by_name.side_effect = Exception("Totally unexpected crash")
    response = app_test_client.get('/stores/search?name=CrashTest')
    assert response.status_code == 500
    json_data = response.get_json()
    assert "An internal server error occurred" in json_data["message"]
