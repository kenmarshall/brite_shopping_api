"""
This file defines the ProductModel class, which provides methods for interacting
with the 'products' collection in the MongoDB database. It includes functionality
to add products, retrieve products, and search by name.
"""

from app.db import db  # Import the database connection
from bson import ObjectId  # Import ObjectId for MongoDB document IDs


class ProductModel:
    """
    A model class for interacting with the 'products' collection in the database.
    Provides methods to add, retrieve, and search products.
    """

    @staticmethod
    def get_or_create_product(data: dict) -> ObjectId:
        """
        Retrieves an existing product by name or adds it to the database if it doesn't exist.

        :param data: A dictionary containing product details (e.g., name, description).
                     Must include "name".
        :return: The _id of the existing or newly inserted product.
        :raises ValueError: If 'name' is missing in the input data.
        """
        product_name = data.get("name")
        if not product_name:
            raise ValueError("Product name ('name' field) is required.")

        # Check for an existing product with the same name (case-sensitive)
        existing_product = db.products.find_one({"name": product_name})

        if existing_product:
            return existing_product["_id"]  # Return ID of existing product
        else:
            # Product not found, create a new one
            # Insert the new product into the database
            result = db.products.insert_one(data)
            return result.inserted_id  # Return the ID of the newly inserted product

    @staticmethod
    def get_one(product_id: str) -> dict:
        """
        Retrieves a single product from the database by its ID.

        :param product_id: The ID of the product to retrieve.
        :return: The product document as a dictionary, or None if not found.
        """
        # Convert the product_id to an ObjectId and query the database
        return db.products.find_one({"_id": ObjectId(product_id)})

    @staticmethod
    def find_by_name(query_name: str) -> list:
        """
        Finds products by name using basic text search.

        :param query_name: The name to search for.
        :return: A list of matching product documents.
        """
        # Use MongoDB text search or regex for basic name matching
        # Case-insensitive search
        regex_pattern = {"$regex": query_name, "$options": "i"}
        products = list(db.products.find({"name": regex_pattern}))
        
        # Convert ObjectId to string for JSON serialization
        for product in products:
            if isinstance(product.get("_id"), ObjectId):
                product["_id"] = str(product["_id"])
        
        return products

    @staticmethod
    def get_all() -> list:
        """
        Retrieves all products from the database.

        :return: A list of all product documents.
        """
        products = list(db.products.find({}))
        for product in products:
            if isinstance(product.get("_id"), ObjectId):
                product["_id"] = str(product["_id"])
        return products
