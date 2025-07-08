"""Unit tests for the Product model."""

import pytest
from datetime import datetime
from brite_catalog_engine.core.product import Product


class TestProduct:
    """Test cases for the Product model."""
    
    def test_product_creation(self):
        """Test basic product creation."""
        product = Product(
            name="Test Product",
            brand="Test Brand",
            price="$19.99",
            description="A test product"
        )
        
        assert product.name == "Test Product"
        assert product.brand == "Test Brand"
        assert product.price == "$19.99"
        assert product.description == "A test product"
        assert product.currency == "JMD"  # Default
        assert isinstance(product.tags, list)
        assert len(product.tags) == 0
    
    def test_product_to_dict(self):
        """Test product serialization to dictionary."""
        product = Product(
            name="Test Product",
            brand="Test Brand",
            price="$19.99"
        )
        
        data = product.to_dict()
        
        assert isinstance(data, dict)
        assert data["name"] == "Test Product"
        assert data["brand"] == "Test Brand"
        assert data["price"] == "$19.99"
        assert "created_at" in data
        assert "updated_at" in data
    
    def test_product_from_dict(self):
        """Test product creation from dictionary."""
        data = {
            "name": "Test Product",
            "brand": "Test Brand",
            "price": "$19.99",
            "description": "A test product",
            "tags": ["electronics", "gadget"]
        }
        
        product = Product.from_dict(data)
        
        assert product.name == "Test Product"
        assert product.brand == "Test Brand"
        assert product.price == "$19.99"
        assert product.description == "A test product"
        assert product.tags == ["electronics", "gadget"]
    
    def test_product_post_init(self):
        """Test post-initialization processing."""
        product = Product(
            name="  Test Product  ",  # Whitespace should be stripped
            brand="  Test Brand  "
        )
        
        assert product.name == "Test Product"
        assert product.brand == "Test Brand"
    
    @pytest.mark.parametrize("name,expected", [
        ("Simple Product", "Simple Product"),
        ("  Whitespace Product  ", "Whitespace Product"),
        ("", ""),
    ])
    def test_name_cleaning(self, name, expected):
        """Test name cleaning during initialization."""
        product = Product(name=name)
        assert product.name == expected 