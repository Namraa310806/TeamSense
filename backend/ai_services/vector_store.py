"""
Vector Store using FAISS for Embeddings
"""
import numpy as np
import os
import pickle

class FaissVectorStore:
    def __init__(self, dim, index_path='vectors.pkl', meta_path='meta.pkl'):
        self.dim = dim
        self.index_path = index_path
        self.meta_path = meta_path
        if os.path.exists(index_path) and os.path.exists(meta_path):
            with open(index_path, 'rb') as f:
                self.vectors = pickle.load(f)
            with open(meta_path, 'rb') as f:
                self.metadata = pickle.load(f)
        else:
            self.vectors = []
            self.metadata = []

    def add(self, vectors, meta):
        self.vectors.extend(vectors)
        self.metadata.extend(meta)
        self.save()

    def search(self, query_vector, top_k=5):
        if not self.vectors:
            return []
        vectors_np = np.array(self.vectors)
        query_np = np.array(query_vector)
        dists = np.linalg.norm(vectors_np - query_np, axis=1)
        top_k_idx = np.argsort(dists)[:top_k]
        return [self.metadata[i] for i in top_k_idx]

    def save(self):
        with open(self.index_path, 'wb') as f:
            pickle.dump(self.vectors, f)
        with open(self.meta_path, 'wb') as f:
            pickle.dump(self.metadata, f)
