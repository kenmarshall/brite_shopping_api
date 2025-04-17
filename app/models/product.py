from app.services.ai_service import ai_service
from app.db import db



# TODO: Need to add some pagination and filtering and indexing name
class ProductModel:
    def __init__(self, collection):
        self.collection = collection

    def get_one(self, product_id):
        product = self.collection.find_one({"_id": str(product_id)})
        return product

    def find_by_name(self, query_name):
        """
        Finds products similar to the given query name using FAISS.
        :param query_name: The name to search for.
        :param top_k: The number of similar products to return.
        :return: List of similar products with similarity scores.
        """
        try:
            # Generate embedding for the query name
            query_embedding = ai_service.generate_embedding(query_name)

            # Perform similarity search using the private method in AIService
            _, indices = ai_service.search_similar(query_embedding, top_k=5)

            # Fetch the corresponding products from the database
            products = list(self.collection.find({"embedding": {"$exists": True}}))
            similar_products = [products[i] for i in indices[0]]

            # Return the similar products
            return similar_products
        except Exception as e:
            raise ValueError(f"Error finding similar products: {e}")

    def get_all(self):
        documents = self.collection.find()

        result = []
        for document in documents:
            document["_id"] = str(document["_id"])
            result.append(document)
        return result

    def add(self, data):
        """
        Adds a new product to the database and generates its embedding.
        """
        try:
            # Generate embedding for the product name
            if "name" in data:
                embedding = ai_service.generate_embedding(data["name"])
                data["embedding"] = embedding

                # Add the embedding to the FAISS index
                ai_service.add_to_index(embedding)

            # Ensure locations field is initialized
            if "locations" not in data:
                data["locations"] = []

            # Insert the product into the database
            self.collection.insert_one(data)
        except Exception as e:
            raise ValueError(f"Error adding product: {e}")


    def add_location(self, product_id, store, price, latitude, longitude, address):
        """
        Adds a store location with price and geographical data to a product.
        """
        try:
            location_data = {
                "store": store,
                "price": price,
                "latitude": latitude,
                "longitude": longitude,
                "address": address
            }

            # Add the location to the product's locations array
            self.collection.update_one(
                {"_id": product_id},
                {"$push": {"locations": location_data}}
            )
        except Exception as e:
            raise ValueError(f"Error adding location: {e}")

product_model = ProductModel(db.products)