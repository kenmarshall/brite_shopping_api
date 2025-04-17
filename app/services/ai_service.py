from sentence_transformers import SentenceTransformer
import numpy as np
import faiss


class AIService:
    def __init__(self):
        # Load a pre-trained SentenceTransformer model
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        self.index = None  # FAISS index for similarity search
        self.embeddings = []  # Store embeddings in memory for incremental updates

    def generate_embedding(self, text):
        """
        Generates an embedding for the given text using SentenceTransformers.
        :param text: The input text.
        :return: The embedding vector.
        """
        return self.embedding_model.encode(text)

    def initialize_faiss_index(self, dimension):
        """
        Initializes a FAISS index for similarity search.
        :param dimension: The dimensionality of the embeddings.
        """
        self.index = faiss.IndexFlatL2(dimension)

    def add_to_index(self, embedding):
        """
        Adds a new embedding to the FAISS index.
        :param embedding: The embedding vector to add.
        """
        if self.index is None:
            # Initialize the FAISS index if it doesn't exist
            dimension = len(embedding)
            self.initialize_faiss_index(dimension)

        # Add the embedding to the FAISS index
        self.index.add(np.array([embedding]))

    def search_similar(self, query_embedding, top_k=5):
        """
        Searches for the most similar embeddings in the FAISS index.
        :param query_embedding: The embedding of the query text.
        :param top_k: The number of similar items to return.
        :return: Distances and indices of the top-k similar items.
        """
        if self.index is None or self.index.ntotal == 0:
            raise ValueError("FAISS index is empty or has not been initialized.")

        distances, indices = self.index.search(np.array([query_embedding]), k=top_k)
        return distances, indices
    
ai_service = AIService()