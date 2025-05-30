"""
This file defines the ProductModel class, which provides methods for interacting
with the 'products' collection in the MongoDB database. It includes functionality
to add products, retrieve products, and find similar products using embeddings.
"""

from app.db import db  # Import the database connection
from bson.objectid import ObjectId  # Import ObjectId for MongoDB document IDs
from app.services.ai_service import AIService  # Import AIService for embedding generation and similarity search


class ProductModel:
    """
    A model class for interacting with the 'products' collection in the database.
    Provides methods to add, retrieve, and find similar products.
    """

    @staticmethod
    def add_product(data: dict) -> ObjectId:
        """
        Adds a new product to the database and generates its embedding.

        :param data: A dictionary containing product details (e.g., name, description, price).
        :return: The _id of the newly inserted product.
        :raises ValueError: If required fields are missing in the input data.
        """
        # Validate input data
        if "name" not in data:
            raise ValueError("Product name is required")

        # Generate embedding for the product name
        ai_service = AIService()
        embedding = ai_service.generate_embedding(data["name"])
        data["embedding"] = embedding  # Add the embedding to the product data

        # Insert the product into the database
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
    def find_by_name(query_name: str, top_k: int = 5) -> list:
        """
        Finds products similar to the given query name using embeddings.

        :param query_name: The name to search for.
        :param top_k: The number of similar products to return.
        :return: A list of similar product documents.
        """
        # Generate an embedding for the query name
        ai_service = AIService()
        query_embedding = ai_service.generate_embedding(query_name)

        # Perform similarity search using the AIService
        indices = ai_service.search_similar(query_embedding, top_k)

        # Fetch the corresponding products from the database
        products = list(db.products.find({"embedding": {"$exists": True}}))
        similar_products = [products[i] for i in indices]

        return similar_products  # Return the list of similar products

product_model = ProductModel()
