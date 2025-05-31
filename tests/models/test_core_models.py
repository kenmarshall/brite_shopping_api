import pytest
from bson import ObjectId
import mongomock
from unittest.mock import MagicMock, patch # Ensure patch is imported
# import sys # sys might not be needed anymore if all sys.modules are in conftest
from datetime import datetime, timezone, timedelta

# app.db is patched by the mock_db fixture
from app.db import db as original_db_module

# Models
from app.models.store_model import StoreModel
from app.models.product_model import ProductModel
from app.models.product_price_model import ProductPriceModel

# NOTE: ai_service and google_maps_service should now be mocked by conftest.py

@pytest.fixture(scope="function")
def mock_db():
    client = mongomock.MongoClient()
    mock_db_instance = client.test_db_unit

    # Patch the collection objects on the imported db module instance
    original_db_module.products = mock_db_instance.products
    original_db_module.stores = mock_db_instance.stores
    original_db_module.product_prices = mock_db_instance.product_prices

    yield mock_db_instance # The test will use this for direct assertions

    # Teardown: Clear collections after each test
    mock_db_instance.products.delete_many({})
    mock_db_instance.stores.delete_many({})
    mock_db_instance.product_prices.delete_many({})
    client.close()

class TestCoreModels:

    # --- StoreModel Tests ---
    def test_store_get_or_create_new(self, mock_db):
        store_data = {"place_id": "new_place1", "store": "New Store", "address": "123 New St"}
        store_id = StoreModel.get_or_create(store_data)
        assert store_id is not None
        created_store = mock_db.stores.find_one({"_id": store_id})
        assert created_store is not None
        assert created_store["place_id"] == "new_place1"
        assert created_store["store"] == "New Store"
        assert created_store["address"] == "123 New St"
        assert mock_db.stores.count_documents({}) == 1

    def test_store_get_or_create_finds_existing_and_updates_fields(self, mock_db): # Combined existing and update test
        initial_id = mock_db.stores.insert_one(
            {"place_id": "existing_place1", "store": "Old Store Name", "address": "Old Address", "other_field": "should_remain"}
        ).inserted_id

        store_data_for_lookup = {"place_id": "existing_place1", "store": "New Store Name", "address": "New Address", "new_field": "added"}

        returned_id = StoreModel.get_or_create(store_data_for_lookup)
        assert returned_id == initial_id

        updated_store = mock_db.stores.find_one({"_id": initial_id})
        assert updated_store["store"] == "New Store Name"
        assert updated_store["address"] == "New Address"
        assert updated_store["other_field"] == "should_remain" # Unchanged by $set if not in data_for_set
        assert updated_store["new_field"] == "added"
        assert mock_db.stores.count_documents({}) == 1

    def test_store_get_or_create_handles_none_values_in_data(self, mock_db):
        store_data = {"place_id": "pID002", "store": "Store With None", "address": None, "link": "http://example.com"}
        store_id = StoreModel.get_or_create(store_data) # The model filters out 'address: None'
        created_store = mock_db.stores.find_one({"_id": store_id})
        assert created_store is not None
        assert created_store["place_id"] == "pID002"
        assert created_store["store"] == "Store With None"
        assert "address" not in created_store # None value was filtered out by model's data_for_set
        assert created_store["link"] == "http://example.com"

    def test_store_get_or_create_missing_place_id(self, mock_db):
        with pytest.raises(ValueError, match="Store place_id is required"):
            StoreModel.get_or_create({"store": "Store Without Place ID"})

    def test_store_get_or_create_missing_store_name(self, mock_db):
        with pytest.raises(ValueError, match="Store name .* required"): # Updated regex for store name error
            StoreModel.get_or_create({"place_id": "place123"})

    # --- ProductModel Tests ---
    def test_product_get_or_create_new_product(self, mock_db):
        # ai_service.generate_embedding is mocked by conftest.py to return [0.1] * 768
        product_data = {"name": "New Unique Product", "description": "A fresh product"}
        product_id = ProductModel.get_or_create_product(product_data)
        assert product_id is not None
        created_product = mock_db.products.find_one({"_id": product_id})
        assert created_product is not None
        assert created_product["name"] == "New Unique Product"
        assert "embedding" in created_product
        assert created_product["embedding"] == [0.1] * 768
        assert mock_db.products.count_documents({}) == 1

    def test_product_get_or_create_existing_product(self, mock_db):
        initial_embedding = [0.2] * 768
        existing_product_id = mock_db.products.insert_one(
            {"name": "Existing Product", "description": "Already here", "embedding": initial_embedding}
        ).inserted_id

        product_data = {"name": "Existing Product", "description": "Updated description attempt"}

        # Patch the ai_service.generate_embedding where it's used by get_or_create_product
        # This is 'app.models.product_model.ai_service'
        with patch('app.models.product_model.ai_service.generate_embedding') as mock_gen_embedding:
            # Ensure the mock from conftest is not further complicating this.
            # The local patch should take precedence.
            mock_gen_embedding.return_value = [0.3] * 768 # Different from conftest to be sure

            returned_id = ProductModel.get_or_create_product(product_data)
            mock_gen_embedding.assert_not_called() # Crucial check: Should not be called for existing product

        assert returned_id == existing_product_id

        product_in_db = mock_db.products.find_one({"_id": existing_product_id})
        assert product_in_db["description"] == "Already here"
        assert product_in_db["embedding"] == initial_embedding # Embedding should be original
        assert mock_db.products.count_documents({}) == 1

    def test_product_get_or_create_missing_name(self, mock_db):
        with pytest.raises(ValueError, match="Product name .* required"): # Updated regex for product name error
            ProductModel.get_or_create_product({"description": "Product without a name"})

    # --- ProductPriceModel Tests ---
    def test_product_price_upsert_new_price(self, mock_db):
        prod_id = ObjectId()
        store_id = ObjectId()
        # Mock product and store existence for FK, though not strictly enforced by current model
        mock_db.products.insert_one({"_id": prod_id, "name": "Test Prod"})
        mock_db.stores.insert_one({"_id": store_id, "name": "Test Store", "place_id": "p1"})

        price_val = 9.99
        currency_val = "USD"
        time_before = datetime.now(timezone.utc) - timedelta(seconds=1)

        price_id = ProductPriceModel.upsert_price(str(prod_id), str(store_id), price_val, currency_val)
        assert price_id is not None

        price_doc = mock_db.product_prices.find_one({"_id": price_id})
        assert price_doc["product_id"] == prod_id
        assert price_doc["store_id"] == store_id
        assert price_doc["price"] == price_val
        assert price_doc["currency"] == currency_val

        retrieved_dt = price_doc["last_updated"]
        if retrieved_dt.tzinfo is None: # Make it timezone-aware if mongomock made it naive
            retrieved_dt = retrieved_dt.replace(tzinfo=timezone.utc)
        assert retrieved_dt > time_before
        assert mock_db.product_prices.count_documents({}) == 1

    def test_product_price_upsert_updates_existing_price(self, mock_db):
        prod_id = ObjectId()
        store_id = ObjectId()
        mock_db.products.insert_one({"_id": prod_id, "name": "Test Prod"})
        mock_db.stores.insert_one({"_id": store_id, "name": "Test Store", "place_id": "p1"})

        initial_price_val = 10.00
        initial_currency = "USD"
        initial_time = datetime.now(timezone.utc) - timedelta(hours=1)

        # Pre-populate price
        existing_price_id = mock_db.product_prices.insert_one({
            "product_id": prod_id,
            "store_id": store_id,
            "price": initial_price_val,
            "currency": initial_currency,
            "last_updated": initial_time
        }).inserted_id

        updated_price_val = 12.50
        updated_currency = "EUR"
        time_before_update = datetime.now(timezone.utc) - timedelta(seconds=1)

        returned_price_id = ProductPriceModel.upsert_price(str(prod_id), str(store_id), updated_price_val, updated_currency)
        assert returned_price_id == existing_price_id # ID should be the same

        price_doc = mock_db.product_prices.find_one({"_id": returned_price_id})
        assert price_doc["price"] == updated_price_val
        assert price_doc["currency"] == updated_currency

        retrieved_dt_updated = price_doc["last_updated"]
        if retrieved_dt_updated.tzinfo is None: # Make it timezone-aware
            retrieved_dt_updated = retrieved_dt_updated.replace(tzinfo=timezone.utc)

        # Ensure initial_time is also UTC aware for the != comparison
        if initial_time.tzinfo is None:
             initial_time_aware = initial_time.replace(tzinfo=timezone.utc) # Should not happen based on test code
        else:
            initial_time_aware = initial_time

        assert retrieved_dt_updated > time_before_update
        assert retrieved_dt_updated != initial_time_aware
        assert mock_db.product_prices.count_documents({}) == 1

    def test_product_price_upsert_with_string_ids_creates_new(self, mock_db): # Test with string IDs for new entry
        prod_id_str = str(ObjectId())
        store_id_str = str(ObjectId())
        # No pre-existing product/store needed in DB for this model's logic,
        # as it doesn't perform lookups on product/store collections.

        price_id = ProductPriceModel.upsert_price(prod_id_str, store_id_str, 20.00, "CAD")
        assert price_id is not None
        price_doc = mock_db.product_prices.find_one({"_id": price_id})
        assert price_doc["product_id"] == ObjectId(prod_id_str)
        assert price_doc["store_id"] == ObjectId(store_id_str)
        assert price_doc["price"] == 20.00
        assert price_doc["currency"] == "CAD"
        assert mock_db.product_prices.count_documents({}) == 1
