import unittest
from unittest.mock import patch, MagicMock
from bson import ObjectId
from flask import Flask

# conftest.py should be mocking app.services.ai_service, etc.
from app.resources.product_resource import ProductResource
# Models are mocked, so direct import of models not strictly needed here, but ProductResource imports them.

class TestProductResourcePost(unittest.TestCase):

    # Patch paths point to where the names are looked up: in product_resource module
    @patch('app.resources.product_resource.ProductPriceModel')
    @patch('app.resources.product_resource.ProductModel')
    @patch('app.resources.product_resource.StoreModel')
    def test_post_product_created_price_inserted(
        self, mock_StoreModel, mock_ProductModel, mock_ProductPriceModel
    ):
        app = Flask(__name__)
        payload = {
            "product_data": {"name": "New Product", "description": "Desc"},
            "store_info": {"place_id": "p1", "name": "Store 1"},
            "price": 10.0, "currency": "USD"
        }
        
        mock_store_id = ObjectId()
        mock_product_id = ObjectId()
        mock_price_id = ObjectId()

        mock_StoreModel.get_or_create.return_value = mock_store_id
        mock_ProductModel.get_or_create_product.return_value = mock_product_id
        mock_ProductPriceModel.upsert_price.return_value = mock_price_id

        resource = ProductResource()
        with app.test_request_context(json=payload):
            response, status_code = resource.post()

        self.assertEqual(status_code, 201)
        expected_response = {
            "message": "Product information processed successfully",
            "product_id": str(mock_product_id),
            "store_id": str(mock_store_id),
            "price_id": str(mock_price_id)
        }
        self.assertEqual(response, expected_response)

        mock_StoreModel.get_or_create.assert_called_once_with(payload["store_info"])
        mock_ProductModel.get_or_create_product.assert_called_once_with(payload["product_data"])
        mock_ProductPriceModel.upsert_price.assert_called_once_with(
            str(mock_product_id), str(mock_store_id), payload["price"], payload["currency"]
        )

    @patch('app.resources.product_resource.ProductPriceModel')
    @patch('app.resources.product_resource.ProductModel')
    @patch('app.resources.product_resource.StoreModel')
    def test_post_product_found_price_updated(
        self, mock_StoreModel, mock_ProductModel, mock_ProductPriceModel
    ):
        app = Flask(__name__)
        payload = {
            "product_data": {"name": "Existing Product"},
            "store_info": {"place_id": "p2", "name": "Store 2"},
            "price": 12.0, "currency": "EUR"
        }

        mock_store_id = ObjectId()
        mock_existing_product_id = ObjectId()
        mock_updated_price_id = ObjectId()

        mock_StoreModel.get_or_create.return_value = mock_store_id
        mock_ProductModel.get_or_create_product.return_value = mock_existing_product_id
        mock_ProductPriceModel.upsert_price.return_value = mock_updated_price_id

        resource = ProductResource()
        with app.test_request_context(json=payload):
            response, status_code = resource.post()

        self.assertEqual(status_code, 201)
        expected_response = {
            "message": "Product information processed successfully",
            "product_id": str(mock_existing_product_id),
            "store_id": str(mock_store_id),
            "price_id": str(mock_updated_price_id)
        }
        self.assertEqual(response, expected_response)
        mock_ProductModel.get_or_create_product.assert_called_once_with(payload["product_data"])
        mock_ProductPriceModel.upsert_price.assert_called_once_with(
            str(mock_existing_product_id), str(mock_store_id), payload["price"], payload["currency"]
        )

    @patch('app.resources.product_resource.StoreModel')
    def test_post_invalid_request_missing_place_id(self, mock_StoreModel):
        app = Flask(__name__)
        payload = {"product_data": {"name": "Test"}, "store_info": {"name": "No Place ID"}, "price": 9.99}
        resource = ProductResource()
        with app.test_request_context(json=payload):
            response, status_code = resource.post()
        self.assertEqual(status_code, 400)
        self.assertIn("Store place_id is required", response["message"])
        mock_StoreModel.get_or_create.assert_not_called()

    @patch('app.resources.product_resource.StoreModel') # Only StoreModel is relevant before validation fail
    def test_post_invalid_request_missing_product_name(self, mock_StoreModel):
        app = Flask(__name__)
        payload = {
            "product_data": {}, # Missing name
            "store_info": {"place_id": "p1", "name": "Some Store"},
            "price": 9.99
        }
        resource = ProductResource()
        with app.test_request_context(json=payload):
            response, status_code = resource.post()
        self.assertEqual(status_code, 400)
        self.assertIn("Product data with name is required", response["message"])
        mock_StoreModel.get_or_create.assert_not_called()


    @patch('app.resources.product_resource.StoreModel') # Only StoreModel is relevant before validation fail
    def test_post_invalid_request_missing_price(self, mock_StoreModel):
        app = Flask(__name__)
        payload = {
            "product_data": {"name": "Test Product"},
            "store_info": {"place_id": "p1", "name": "Some Store"}
            # Missing price
        }
        resource = ProductResource()
        with app.test_request_context(json=payload):
            response, status_code = resource.post()
        self.assertEqual(status_code, 400)
        self.assertIn("Price is required and must be a number", response["message"])
        mock_StoreModel.get_or_create.assert_not_called()


    @patch('app.resources.product_resource.ProductPriceModel')
    @patch('app.resources.product_resource.ProductModel')
    @patch('app.resources.product_resource.StoreModel')
    def test_post_store_model_value_error(
        self, mock_StoreModel, mock_ProductModel, mock_ProductPriceModel
    ):
        app = Flask(__name__)
        payload = {"product_data": {"name": "Test Prod"}, "store_info": {"place_id": "p1", "name": "Test Store"}, "price": 9.99}

        mock_StoreModel.get_or_create.side_effect = ValueError("StoreModel internal error")

        resource = ProductResource()
        with app.test_request_context(json=payload):
            response, status_code = resource.post()

        self.assertEqual(status_code, 400)
        self.assertIn("StoreModel internal error", response["message"])
        mock_ProductModel.get_or_create_product.assert_not_called()
        mock_ProductPriceModel.upsert_price.assert_not_called()

if __name__ == '__main__':
    unittest.main()
