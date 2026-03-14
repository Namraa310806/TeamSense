"""
Vector Store backed by FAISS with a numpy fallback.
"""
import numpy as np
import os
import pickle

try:
    import faiss
except Exception:  # pragma: no cover
    faiss = None

class FaissVectorStore:
    def __init__(self, dim, index_path='vectors.pkl', meta_path='meta.pkl'):
        self.dim = dim
        self.index_path = index_path
        self.meta_path = meta_path
        self.metadata = []
        self.vectors = []
        self.use_faiss = faiss is not None

        if self.use_faiss:
            if os.path.exists(index_path) and os.path.exists(meta_path):
                self.index = faiss.read_index(index_path)
                with open(meta_path, 'rb') as f:
                    self.metadata = pickle.load(f)
            else:
                self.index = faiss.IndexFlatL2(dim)
        else:
            if os.path.exists(index_path) and os.path.exists(meta_path):
                with open(index_path, 'rb') as f:
                    self.vectors = pickle.load(f)
                with open(meta_path, 'rb') as f:
                    self.metadata = pickle.load(f)

    def add(self, vectors, meta):
        if self.use_faiss:
            vectors_np = np.array(vectors, dtype=np.float32)
            if vectors_np.ndim == 1:
                vectors_np = vectors_np.reshape(1, -1)
            self.index.add(vectors_np)
        else:
            self.vectors.extend(np.array(vectors, dtype=np.float32).tolist())
        self.metadata.extend(meta)
        self.save()

    def search(self, query_vector, top_k=5):
        if not self.metadata:
            return []

        if self.use_faiss:
            query_np = np.array(query_vector, dtype=np.float32).reshape(1, -1)
            _, indices = self.index.search(query_np, min(top_k, len(self.metadata)))
            valid = [int(i) for i in indices[0] if i >= 0]
            return [self.metadata[i] for i in valid]

        vectors_np = np.array(self.vectors, dtype=np.float32)
        query_np = np.array(query_vector, dtype=np.float32)
        dists = np.linalg.norm(vectors_np - query_np, axis=1)
        top_k_idx = np.argsort(dists)[:top_k]
        return [self.metadata[int(i)] for i in top_k_idx]

    def save(self):
        if self.use_faiss:
            faiss.write_index(self.index, self.index_path)
        else:
            with open(self.index_path, 'wb') as f:
                pickle.dump(self.vectors, f)
        with open(self.meta_path, 'wb') as f:
            pickle.dump(self.metadata, f)
