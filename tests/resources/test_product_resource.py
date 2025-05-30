import sys
import unittest
from unittest.mock import patch, MagicMock
from bson import ObjectId
import json
from flask import Flask # Add Flask import

# Mock heavy dependencies before they are imported by app code
MOCK_MODULES = [
    "faiss",
    "sentence_transformers",
    "app.services.ai_service",
    "app.services.google_maps_service",
    # Add other problematic modules here if they appear
]
for mod_name in MOCK_MODULES:
    sys.modules[mod_name] = MagicMock()

# Assuming app.resources.product_resource and models are discoverable
from app.resources.product_resource import ProductResource

# Flask and flask_restful are not strictly needed for these tests if we mock request
# but if ProductResource relied on app context, we might need a test app.

class TestProductResourcePost(unittest.TestCase):

    @patch('app.resources.product_resource.product_price_model')
    @patch('app.resources.product_resource.product_model')
    @patch('app.resources.product_resource.store_model')
    # Removed @patch('app.resources.product_resource.request')
    def test_post_successful_creation_new_store(
        self, mock_store_model, mock_product_model, mock_product_price_model # mock_request removed
    ):
        app = Flask(__name__) # Dummy app for context
        payload = {
            "product_data": {"name": "Test Product", "description": "A great product"},
            "store_info": {"place_id": "new_place_123", "name": "Test Store", "address": "123 Test St"},
            "price": 9.99,
            "currency": "USD"
        }
        
        # request.get_json() will now use the json from test_request_context

        mock_store_id = ObjectId()
        mock_product_id = ObjectId()

        mock_store_model.get_or_create.return_value = mock_store_id
        mock_product_model.add_product.return_value = mock_product_id
        mock_product_price_model.add_price.return_value = None

        resource = ProductResource()
        with app.test_request_context(json=payload): # Set up request context
            response, status_code = resource.post()

        self.assertEqual(status_code, 201)
        expected_response_data = {
            "message": "Product created successfully",
            "product_id": str(mock_product_id),
            "store_id": str(mock_store_id)
        }
        # Assuming response is a dict, not a Flask Response object with .json attribute
        # If it's a Flask Response, this would be response.json
        self.assertEqual(response, expected_response_data)

        mock_store_model.get_or_create.assert_called_once_with(payload["store_info"])
        mock_product_model.add_product.assert_called_once_with(payload["product_data"])
        mock_product_price_model.add_price.assert_called_once_with(
            mock_product_id, mock_store_id, payload["price"], payload["currency"]
        )

    @patch('app.resources.product_resource.product_price_model')
    @patch('app.resources.product_resource.product_model')
    @patch('app.resources.product_resource.store_model')
    # Removed @patch('app.resources.product_resource.request')
    def test_post_successful_creation_existing_store(
        self, mock_store_model, mock_product_model, mock_product_price_model # mock_request removed
    ):
        app = Flask(__name__) # Dummy app for context
        payload = {
            "product_data": {"name": "Another Product"},
            "store_info": {"place_id": "existing_place_456", "name": "Known Store"},
            "price": 19.99
            # Currency will default to JMD
        }
        # request.get_json() will now use the json from test_request_context

        mock_existing_store_id = ObjectId()
        mock_new_product_id = ObjectId()

        mock_store_model.get_or_create.return_value = mock_existing_store_id
        mock_product_model.add_product.return_value = mock_new_product_id

        resource = ProductResource()
        with app.test_request_context(json=payload):
            response, status_code = resource.post()

        self.assertEqual(status_code, 201)
        self.assertEqual(response["product_id"], str(mock_new_product_id))
        self.assertEqual(response["store_id"], str(mock_existing_store_id))

        mock_store_model.get_or_create.assert_called_once_with(payload["store_info"])
        mock_product_model.add_product.assert_called_once_with(payload["product_data"])
        mock_product_price_model.add_price.assert_called_once_with(
            mock_new_product_id, mock_existing_store_id, payload["price"], "JMD" # Default currency
        )

    @patch('app.resources.product_resource.product_price_model')
    @patch('app.resources.product_resource.product_model')
    @patch('app.resources.product_resource.store_model')
    # Removed @patch('app.resources.product_resource.request')
    def test_post_invalid_request_missing_place_id(
        self, mock_store_model, mock_product_model, mock_product_price_model # mock_request removed
    ):
        app = Flask(__name__) # Dummy app for context
        payload = {
            "product_data": {"name": "Test Product"},
            "store_info": {"name": "Store without place_id"}, # Missing place_id
            "price": 9.99
        }
        # request.get_json() will now use the json from test_request_context

        resource = ProductResource()
        with app.test_request_context(json=payload):
            response, status_code = resource.post()

        self.assertEqual(status_code, 400)
        self.assertIn("Store place_id is required", response["message"])

        mock_store_model.get_or_create.assert_not_called()
        mock_product_model.add_product.assert_not_called()
        mock_product_price_model.add_price.assert_not_called()

    @patch('app.resources.product_resource.product_price_model')
    @patch('app.resources.product_resource.product_model')
    @patch('app.resources.product_resource.store_model')
    # Removed @patch('app.resources.product_resource.request')
    def test_post_invalid_request_missing_price(
        self, mock_store_model, mock_product_model, mock_product_price_model # mock_request removed
    ):
        app = Flask(__name__) # Dummy app for context
        payload = {
            "product_data": {"name": "Test Product"},
            "store_info": {"place_id": "place123", "name": "Test Store"}
            # Missing price
        }
        # request.get_json() will now use the json from test_request_context

        resource = ProductResource()
        with app.test_request_context(json=payload):
            response, status_code = resource.post()

        self.assertEqual(status_code, 400)
        self.assertIn("Price is required and must be a number", response["message"])

        mock_store_model.get_or_create.assert_not_called()
        mock_product_model.add_product.assert_not_called()
        mock_product_price_model.add_price.assert_not_called()

    @patch('app.resources.product_resource.product_price_model')
    @patch('app.resources.product_resource.product_model')
    @patch('app.resources.product_resource.store_model')
    # Removed @patch('app.resources.product_resource.request')
    def test_post_invalid_request_missing_product_name(
        self, mock_store_model, mock_product_model, mock_product_price_model # mock_request removed
    ):
        app = Flask(__name__) # Dummy app for context
        payload = {
            "product_data": {"description": "Product without name"}, # Missing name
            "store_info": {"place_id": "place123", "name": "Test Store"},
            "price": 10.00
        }
        # request.get_json() will now use the json from test_request_context

        resource = ProductResource()
        with app.test_request_context(json=payload):
            response, status_code = resource.post()

        self.assertEqual(status_code, 400)
        self.assertIn("Product data with name is required", response["message"])

        mock_store_model.get_or_create.assert_not_called()
        mock_product_model.add_product.assert_not_called()
        mock_product_price_model.add_price.assert_not_called()

    @patch('app.resources.product_resource.product_price_model')
    @patch('app.resources.product_resource.product_model')
    @patch('app.resources.product_resource.store_model')
    # Removed @patch('app.resources.product_resource.request')
    def test_post_store_model_value_error(
        self, mock_store_model, mock_product_model, mock_product_price_model # mock_request removed
    ):
        app = Flask(__name__) # Dummy app for context
        payload = {
            "product_data": {"name": "Test Product"},
            "store_info": {"place_id": "valid_place_id", "name": "Test Store"}, # This will be passed to store_model
            "price": 9.99
        }
        # request.get_json() will now use the json from test_request_context

        # Simulate store_model.get_or_create raising a ValueError (e.g., internal validation)
        mock_store_model.get_or_create.side_effect = ValueError("Something went wrong in store_model")

        resource = ProductResource()
        with app.test_request_context(json=payload):
            response, status_code = resource.post()

        self.assertEqual(status_code, 400) # As per the ValueError handling in ProductResource
        self.assertIn("Something went wrong in store_model", response["message"])

        mock_store_model.get_or_create.assert_called_once_with(payload["store_info"])
        mock_product_model.add_product.assert_not_called()
        mock_product_price_model.add_price.assert_not_called()


if __name__ == '__main__':
    unittest.main()
