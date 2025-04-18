import os
from bson import ObjectId
import faiss
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer


class AIService:
    def __init__(self, model_name="all-MiniLM-L6-v2", index_dir="embeddings_index"):
        self.dim = 384
        self.index_dir = index_dir
        self.index_file = os.path.join(index_dir, "faiss.index")
        self.metadata_file = os.path.join(index_dir, "metadata.pkl")
        os.makedirs(index_dir, exist_ok=True)

        # Load model
        self.model = SentenceTransformer(model_name)

        # Load or initialize FAISS index
        if os.path.exists(self.index_file):
            self.index = faiss.read_index(self.index_file)
        else:
            self.index = faiss.IndexFlatL2(self.dim)

        # Load or initialize doc_ids
        if os.path.exists(self.metadata_file):
            with open(self.metadata_file, "rb") as f:
                self.doc_ids = pickle.load(f)
        else:
            self.doc_ids = []

    def generate_embedding(self, name):
        embedding = self.model.encode(name).astype("float32").reshape(1, -1)
        return embedding

    def add_to_index(self, embedding, doc_id):
        self.index.add(embedding)
        self.doc_ids.append(str(doc_id))
        self._persist()

    def search_similar(self, query_embedding, top_k=5):
        if self.index.ntotal == 0 or len(self.doc_ids) == 0:
            return [], []

        distances, indices = self.index.search(query_embedding, top_k)

        matched_ids = []
        for row in indices:
            matched_row = []
            for i in row:
                if 0 <= i < len(self.doc_ids):
                    matched_row.append(self.doc_ids[i])
            matched_ids.append(matched_row)

        return distances, matched_ids

    def _persist(self):
        faiss.write_index(self.index, self.index_file)
        with open(self.metadata_file, "wb") as f:
            pickle.dump(self.doc_ids, f)
    
    def rebuild_index_from_db(self, products_collection):

        print("Rebuilding FAISS index from MongoDB...")

        products = list(products_collection.find({"embedding": {"$exists": True}}))
        if not products:
            print("No embeddings found in database.")
            return

        # Reset index
        self.index = faiss.IndexFlatL2(self.dim)
        self.doc_ids = []

        vectors = []
        for p in products:
            vectors.append(np.array(p["embedding"], dtype="float32"))
            self.doc_ids.append(str(p["_id"]))

        embeddings = np.vstack(vectors)
        self.index.add(embeddings)
        self._persist()

        print(f"Rebuilt FAISS index with {len(products)} entries.")


# Instantiate the service
ai_service = AIService()
