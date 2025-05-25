from bson import ObjectId
from app.services.ai_service import ai_service
from app.db import db


# TODO: Need to add some pagination and filtering and indexing name
class ProductModel:
    def __init__(self, collection):
        self.collection = collection

    def add(self, data):
        """
        Adds a new product to the database and indexes it for similarity search.
        """
        try:
            name = data.get("name")
            if not name:
                raise ValueError("Product name is required")

            # Generate embedding for the product name
            embedding = ai_service.generate_embedding(name)
            data["embedding"] = embedding.flatten().tolist()

            # Ensure locations field is initialized
            if "locations" not in data:
                data["locations"] = []

            # Insert the product into MongoDB
            result = self.collection.insert_one(data)

            # Add the embedding to FAISS index with Mongo _id
            ai_service.add_to_index(embedding, result.inserted_id)

            return str(result.inserted_id)
        except Exception as e:
            raise ValueError(f"Error adding product: {e}")

    def get_one(self, product_id):
        try:
            product = self.collection.find_one({"_id": ObjectId(product_id)})
            if product:
                product["_id"] = str(product["_id"])
            return product
        except Exception:
            return None

    def get_all(self):
        documents = self.collection.find()

        result = []
        for document in documents:
            document["_id"] = str(document["_id"])
            result.append(document)
        return result

    def find_by_name(self, name, top_k=5):
        """
        Finds top-k products most similar to the given name using FAISS.
        Returns list of products with similarity scores and the embedding.
        """
        try:
            embedding = ai_service.generate_embedding(name)
            distances, matched_ids = ai_service.search_similar(embedding, top_k=top_k)

            if not matched_ids or not matched_ids[0]:
                return []

            ids = [ObjectId(pid) for pid in matched_ids[0]]
            docs = list(self.collection.find({"_id": {"$in": ids}}, {"embedding": 0}))
            doc_map = {str(doc["_id"]): doc for doc in docs}
            similar_products = []

            for i, pid in enumerate(matched_ids[0]):
                pid_str = str(pid)
                doc = doc_map.get(pid_str)
                if doc:
                    doc["_id"] = pid_str
                    doc["similarity"] = float(distances[0][i])
                    similar_products.append(doc)

            return similar_products

        except Exception as e:
            raise ValueError(f"Error finding similar products: {e}")
        except Exception as e:
            raise ValueError(f"Error finding similar products: {e}")


product_model = ProductModel(db.products)
