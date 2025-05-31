import pytest
from pymongo import MongoClient
from bson import ObjectId
import mongomock # For mocking MongoDB

# Mock the db connection before models are imported
# This is a common pattern for testing with a mocked database.
# We need to ensure 'app.db.db' is patched BEFORE StoreModel, ProductModel, etc. are imported.
# One way to achieve this is to set up the mock in a conftest.py or at the very top of the test file.

# For simplicity here, we'll assume app.db can be influenced by an environment variable
# or we can directly patch it. Let's try direct patching for this subtask.

from app.db import db as original_db_module # Keep a reference if needed, or ensure it's not used

# Mock AIService before ProductModel imports it
from unittest.mock import MagicMock
import sys
mock_ai_service = MagicMock()
def mock_generate_embedding(text):
    # Return a fixed-length list of floats as a dummy embedding
    return [0.1] * 768 # Assuming embedding dimension, adjust if known or necessary
mock_ai_service.generate_embedding = mock_generate_embedding
sys.modules['app.services.ai_service'] = MagicMock(ai_service=mock_ai_service)


# Now import models AFTER patching dependencies
from app.models.store_model import StoreModel
from app.models.product_model import ProductModel
from app.models.product_price_model import ProductPriceModel

@pytest.fixture(scope="function")
def mock_db():
    # Use mongomock for a clean, in-memory MongoDB for each test function
    client = mongomock.MongoClient()
    mock_db_instance = client.test_db_unit

    # Monkeypatch the 'db' object in app.db module
    # This is a critical step: ensure 'app.db.db' points to our mock_db_instance
    # The original 'db.py' likely does something like:
    # client = MongoClient(os.getenv("MONGO_URI"))
    # db = client.get_default_database() # or client[DB_NAME]
    # We need to replace 'db' that models will use.
    original_db_module.products = mock_db_instance.products
    original_db_module.stores = mock_db_instance.stores
    original_db_module.product_prices = mock_db_instance.product_prices

    yield mock_db_instance

    # Teardown: Clear collections after each test
    mock_db_instance.products.delete_many({})
    mock_db_instance.stores.delete_many({})
    mock_db_instance.product_prices.delete_many({})
    client.close()


class TestCoreModels:

    def test_store_get_or_create_new(self, mock_db):
        store_data = {
            "store": "New Store",
            "place_id": "place123",
            "address": "123 Main St"
        }
        store_id = StoreModel.get_or_create(store_data)
        assert store_id is not None
        created_store = mock_db.stores.find_one({"_id": store_id})
        assert created_store is not None
        assert created_store["store"] == "New Store"
        assert created_store["place_id"] == "place123"

    def test_store_get_or_create_existing(self, mock_db):
        # First, create a store
        initial_store_data = {
            "store": "Existing Store",
            "place_id": "place456",
            "address": "456 Oak Ave"
        }
        # Ensure the store is created using the logic that sets all fields
        # The model's get_or_create uses $setOnInsert, so we need to match its behavior
        # For an existing store, we only need to match on 'store' name as per current StoreModel
        mock_db.stores.insert_one({
            "store": "Existing Store",
            "place_id": "place456",
            "address": "456 Oak Ave",
            "other_field": "value" # To check if $setOnInsert preserves other fields if we were to update
        })

        # Now, try to get or create with the same store name but potentially different/missing other data
        # The current StoreModel.get_or_create matches on "store" (name) only for the find part
        # and uses place_id from store_data for $setOnInsert if new.
        # Let's test based on the provided StoreModel logic.
        # The model's get_or_create uses {"store": store_name} as filter.

        store_data_to_find = {
            "store": "Existing Store", # Matching name
            "place_id": "place456",    # This must be provided for $setOnInsert, but find is by name
                                       # If store name is unique, place_id would be the same.
                                       # If store name not unique, then place_id should be part of the filter.
                                       # Current StoreModel matches on name, then upserts with place_id.
                                       # This test assumes store name is the primary key for finding.
        }

        retrieved_store_id = StoreModel.get_or_create(store_data_to_find)

        assert retrieved_store_id is not None

        found_store = mock_db.stores.find_one({"_id": retrieved_store_id})
        assert found_store is not None
        assert found_store["store"] == "Existing Store"
        assert found_store["place_id"] == "place456" # Should be the original place_id
        assert mock_db.stores.count_documents({"store": "Existing Store"}) == 1


    def test_store_get_or_create_missing_place_id(self, mock_db):
        with pytest.raises(ValueError, match="Store place_id is required"):
            StoreModel.get_or_create({"store": "Store Without Place ID"})

    def test_product_add_product(self, mock_db):
        # ai_service is mocked globally at the start of this file
        product_data = {"name": "Test Product", "description": "A cool product"}
        product_id = ProductModel.add_product(product_data)
        assert product_id is not None
        created_product = mock_db.products.find_one({"_id": product_id})
        assert created_product is not None
        assert created_product["name"] == "Test Product"
        assert "embedding" in created_product # Check that embedding was added
        assert created_product["embedding"] == [0.1] * 768 # Check dummy embedding

    def test_product_add_product_missing_name(self, mock_db):
        with pytest.raises(ValueError, match="Product name is required"):
            ProductModel.add_product({"description": "Product without a name"})

    def test_product_price_add_price(self, mock_db):
        # Create dummy product and store IDs for linking
        # In a real scenario, these would come from adding a product and store first
        test_product_id = ObjectId()
        test_store_id = ObjectId()
        price = 12.99
        currency = "EUR"

        # Insert dummy product and store for FK reference if ProductPriceModel checks existence (it doesn't currently)
        mock_db.products.insert_one({"_id": test_product_id, "name": "Dummy Product"})
        mock_db.stores.insert_one({"_id": test_store_id, "name": "Dummy Store", "place_id": "dummy_place"})

        ProductPriceModel.add_price(str(test_product_id), str(test_store_id), price, currency)

        price_entry = mock_db.product_prices.find_one({
            "product_id": test_product_id,
            "store_id": test_store_id
        })
        assert price_entry is not None
        assert price_entry["price"] == price
        assert price_entry["currency"] == currency
        assert "last_updated" in price_entry
