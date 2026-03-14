"""
Embedding Service for Semantic Search
Uses direct Hugging Face transformers mean pooling (no sentence-transformers)
"""

import logging
import torch
import numpy as np

from ai_engine.model_loader import ModelManager, mean_pool

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self, model_name='sentence-transformers/all-MiniLM-L6-v2'):
        self.model_name = model_name

    def _fallback_embed(self, batch, single):
        vectors = []
        for text in batch:
            seed = abs(hash(text)) % (2**32)
            rng = np.random.default_rng(seed)
            vec = rng.normal(size=384).astype(np.float32)
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            vectors.append(vec)
        return vectors[0] if single else np.array(vectors, dtype=np.float32)

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
        try:
            bundle = ModelManager.get_embedding_bundle()
            tokenizer = bundle['tokenizer']
            model = bundle['model']
            encoded = tokenizer(
                batch,
                padding=True,
                truncation=True,
                return_tensors='pt',
            )
            with torch.no_grad():
                output = model(**encoded)
                embeddings = mean_pool(output.last_hidden_state, encoded['attention_mask'])

            vectors = embeddings.cpu().numpy().astype(np.float32)
            return vectors[0] if single else vectors
        except Exception as exc:
            logger.warning('Embedding generation failed; using deterministic fallback: %s', exc)
            return self._fallback_embed(batch, single)
