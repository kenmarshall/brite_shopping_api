"""
This file defines the ProductModel class, which provides methods for interacting
with the 'products' collection in the MongoDB database. It includes functionality
to add products, retrieve products, and find similar products using embeddings.
"""

from app.db import db  # Import the database connection
from bson.objectid import ObjectId  # Import ObjectId for MongoDB document IDs
from app.services.ai_service import ai_service  # Import AIService for embedding generation and similarity search


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
        query_embedding = ai_service.generate_embedding(query_name)

        # Perform similarity search using the AIService
        # search_similar returns distances, matched_ids
        # matched_ids is a list of lists of doc_ids. For a single query, it's like [['id1', 'id2', ...]]
        _, matched_id_lists = ai_service.search_similar(query_embedding, top_k)

        similar_products = []
        # If search_similar returns nothing or an empty list for the first query
        if not matched_id_lists or not matched_id_lists[0]:
            return similar_products

        # Process the first list of matched IDs (assuming single query search)
        # Fetch products one by one to maintain the order from FAISS.
        # This also ensures that if a product ID from FAISS is somehow stale and not in DB, it's skipped.
        for product_id_str in matched_id_lists[0]:
            product = db.products.find_one({"_id": ObjectId(product_id_str)})
            if product:
                # Optionally, convert ObjectId to string if that's the expected output format for downstream consumers
                # For now, keeping it as is from the database.
                similar_products.append(product)

        return similar_products

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
            # Potentially convert other ObjectId fields if necessary
        return products
