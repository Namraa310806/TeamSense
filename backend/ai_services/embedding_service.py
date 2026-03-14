"""
Embedding Service for Semantic Search
Uses sentence-transformers/all-MiniLM-L6-v2
"""

from sentence_transformers import SentenceTransformer
import numpy as np

class EmbeddingService:
    def __init__(self, model_name='sentence-transformers/all-MiniLM-L6-v2'):
        self.model = SentenceTransformer(model_name)

    def embed_text(self, text):
        if isinstance(text, str):
            return self.model.encode([text])[0]
        elif isinstance(text, list):
            return self.model.encode(text)
        else:
            raise ValueError('Input must be a string or list of strings')
