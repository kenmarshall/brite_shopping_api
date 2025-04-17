import uuid
from services.openai import openai
from sklearn.metrics.pairwise import cosine_similarity

# TODO: Need to add some pagination and filtering and indexing name


class ProductModel:
    def __init__(self, collection):
        self.collection = collection

    def get_one(self, product_id):
        product = self.collection.find_one({"_id": uuid.UUID(product_id)})
        return product

    def find_by_name(self, query_name):
        # Step 1: Generate embedding for the query name
        query_embedding = self._generate_embedding(query_name)

        # Step 2: Fetch all products and their embeddings
        products = list(self.collection.find({"embedding": {"$exists": True}}))
        product_embeddings = [product["embedding"] for product in products]

        # Step 3: Compute similarity scores
        similarities = cosine_similarity([query_embedding], product_embeddings)[0]

        # Step 4: Sort products by similarity
        sorted_products = sorted(
            zip(products, similarities), key=lambda x: x[1], reverse=True
        )

        # Step 5: Return top N similar products
        top_products = [
            {**product, "similarity": similarity}
            for product, similarity in sorted_products[:5]
        ]
        return top_products

    def get_all(self):
        documents = self.collection.find()

        result = []
        for document in documents:
            document["_id"] = str(document["_id"])
            result.append(document)
        return result

    def add(self, data):
        # - TODO: add data validation
        try:
            if "name" in data:
                embedding = self._generate_embedding(data["name"])
                data["embedding"] = embedding

            self.collection.insert_one(data)
        except Exception as e:
            raise ValueError(f"Error adding product: {e}")

    def _generate_embedding(self, text):
        response = openai.Embedding.create(input=text, model="text-embedding-ada-002")
        return response["data"][0]["embedding"]
