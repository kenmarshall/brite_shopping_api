import pytest
from bson import ObjectId
import mongomock
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta

# app.db is patched by the mock_db fixture
from app.db import db as original_db_module

# Models
from app.models.store_model import StoreModel
from app.models.product_model import ProductModel
from app.models.product_price_model import ProductPriceModel

@pytest.fixture(scope="function")
def mock_db():
    client = mongomock.MongoClient()
    mock_db_instance = client.test_db_unit

    # Patch the collection objects on the imported db module instance
    setattr(original_db_module, 'products', mock_db_instance.products)
    setattr(original_db_module, 'stores', mock_db_instance.stores)
    setattr(original_db_module, 'product_prices', mock_db_instance.product_prices)

    yield mock_db_instance # The test will use this for direct assertions

    # Teardown: Clear collections after each test
    mock_db_instance.products.delete_many({})
    mock_db_instance.stores.delete_many({})
    mock_db_instance.product_prices.delete_many({})
    client.close()

# Tests for StoreModel

def test_store_get_or_create_new_store(mock_db):
    """Test creating a new store when it doesn't exist."""
    store_data = {
        "place_id": "place_123",
        "store": "Test Store",
        "address": "123 Test St",
        "latitude": 18.0,
        "longitude": -76.8
    }
    
    store_id = StoreModel.get_or_create(store_data)
    
    # Verify the store was created
    assert store_id is not None
    created_store = mock_db.stores.find_one({"_id": store_id})
    assert created_store["place_id"] == "place_123"
    assert created_store["store"] == "Test Store"
    assert created_store["address"] == "123 Test St"

def test_store_get_or_create_existing_store(mock_db):
    """Test retrieving an existing store."""
    # Pre-insert a store
    existing_store = {
        "place_id": "place_456",
        "store": "Existing Store",
        "address": "456 Existing Ave"
    }
    insert_result = mock_db.stores.insert_one(existing_store)
    existing_id = insert_result.inserted_id
    
    # Call get_or_create with the same place_id
    store_data = {
        "place_id": "place_456",
        "store": "Updated Store Name",  # This should update the existing store
        "address": "456 Updated Ave"
    }
    
    returned_id = StoreModel.get_or_create(store_data)
    
    # Should return the same ID
    assert returned_id == existing_id
    
    # Verify the store was updated
    updated_store = mock_db.stores.find_one({"_id": existing_id})
    assert updated_store["store"] == "Updated Store Name"
    assert updated_store["address"] == "456 Updated Ave"

# Tests for ProductModel

def test_product_get_or_create_new_product(mock_db):
    """Test creating a new product when it doesn't exist."""
    product_data = {
        "name": "Test Product",
        "brand": "Test Brand",
        "description": "A test product"
    }
    
    product_id = ProductModel.get_or_create_product(product_data)
    
    # Verify the product was created
    assert product_id is not None
    created_product = mock_db.products.find_one({"_id": product_id})
    assert created_product["name"] == "Test Product"
    assert created_product["brand"] == "Test Brand"
    assert created_product["description"] == "A test product"

def test_product_get_or_create_existing_product(mock_db):
    """Test retrieving an existing product by name."""
    # Pre-insert a product
    existing_product_data = {
        "name": "Existing Product", 
        "description": "Already here"
    }
    insert_result = mock_db.products.insert_one(existing_product_data)
    existing_id = insert_result.inserted_id
    
    # Try to create the same product
    new_product_data = {"name": "Existing Product", "brand": "Some Brand"}
    returned_id = ProductModel.get_or_create_product(new_product_data)
    
    # Should return the existing ID, not create a new product
    assert returned_id == existing_id
    
    # Verify only one product exists with this name
    products_with_name = list(mock_db.products.find({"name": "Existing Product"}))
    assert len(products_with_name) == 1

def test_product_find_by_name(mock_db):
    """Test searching for products by name."""
    # Insert test products
    products = [
        {"name": "Apple Juice", "brand": "Brand A"},
        {"name": "Orange Juice", "brand": "Brand B"}, 
        {"name": "Apple Sauce", "brand": "Brand C"}
    ]
    mock_db.products.insert_many(products)
    
    # Search for products containing "Apple"
    results = ProductModel.find_by_name("Apple")
    
    # Should find 2 products
    assert len(results) == 2
    names = [p["name"] for p in results]
    assert "Apple Juice" in names
    assert "Apple Sauce" in names

# Tests for ProductPriceModel

def test_product_price_upsert_new_price(mock_db):
    """Test adding a new price for a product at a store."""
    # Create test product and store
    product_id = mock_db.products.insert_one({"name": "Test Product"}).inserted_id
    store_id = mock_db.stores.insert_one({"name": "Test Store"}).inserted_id
    
    # Add price
    price_id = ProductPriceModel.upsert_price(str(product_id), str(store_id), 100.0, "JMD")
    
    # Verify price was created
    assert price_id is not None
    created_price = mock_db.product_prices.find_one({"_id": price_id})
    assert created_price["product_id"] == product_id
    assert created_price["store_id"] == store_id
    assert created_price["price"] == 100.0
    assert created_price["currency"] == "JMD"

def test_product_price_upsert_existing_price(mock_db):
    """Test updating an existing price."""
    # Create test product and store
    product_id = mock_db.products.insert_one({"name": "Test Product"}).inserted_id
    store_id = mock_db.stores.insert_one({"name": "Test Store"}).inserted_id
    
    # Add initial price
    initial_price_id = ProductPriceModel.upsert_price(str(product_id), str(store_id), 100.0, "JMD")
    
    # Update the price
    updated_price_id = ProductPriceModel.upsert_price(str(product_id), str(store_id), 150.0, "JMD")
    
    # Should return the same price document ID
    assert updated_price_id == initial_price_id
    
    # Verify price was updated
    updated_price = mock_db.product_prices.find_one({"_id": updated_price_id})
    assert updated_price["price"] == 150.0
    
    # Verify only one price record exists for this product-store combination
    price_count = mock_db.product_prices.count_documents({
        "product_id": product_id, 
        "store_id": store_id
    })
    assert price_count == 1
