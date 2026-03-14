"""
Embedding Service for Semantic Search
Uses direct Hugging Face transformers mean pooling (no sentence-transformers)
"""

import torch
from transformers import AutoModel, AutoTokenizer
import numpy as np


class EmbeddingService:
    def __init__(self, model_name='sentence-transformers/all-MiniLM-L6-v2'):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.model.eval()

    @staticmethod
    def _mean_pool(last_hidden_state, attention_mask):
        mask = attention_mask.unsqueeze(-1).expand(last_hidden_state.size()).float()
        masked = last_hidden_state * mask
        summed = torch.sum(masked, dim=1)
        counts = torch.clamp(mask.sum(dim=1), min=1e-9)
        return summed / counts

    def embed_text(self, text):
        if isinstance(text, str):
            batch = [text]
            single = True
        elif isinstance(text, list):
            batch = text
            single = False
        else:
            raise ValueError('Input must be a string or list of strings')

        if not batch:
            return []

        encoded = self.tokenizer(
            batch,
            padding=True,
            truncation=True,
            return_tensors='pt',
        )
        with torch.no_grad():
            output = self.model(**encoded)
            embeddings = self._mean_pool(output.last_hidden_state, encoded['attention_mask'])

        vectors = embeddings.cpu().numpy().astype(np.float32)
        return vectors[0] if single else vectors
