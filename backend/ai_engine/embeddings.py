"""Embedding generation using OpenAI with random vector fallback."""
import os
import logging
import numpy as np

logger = logging.getLogger(__name__)

EMBEDDING_DIM = 1536


def generate_embedding(text: str) -> list:
    """Generate an embedding vector for the given text.

    Uses OpenAI text-embedding-ada-002 if API key is available,
    otherwise generates a deterministic pseudo-random vector for demo.
    """
    api_key = os.getenv('OPENAI_API_KEY', '')

    if api_key:
        try:
            return _openai_embedding(text, api_key)
        except Exception as e:
            logger.warning(f"OpenAI embedding failed, using fallback: {e}")

    return _fallback_embedding(text)


def _openai_embedding(text: str, api_key: str) -> list:
    """Generate embedding using OpenAI."""
    from openai import OpenAI
    client = OpenAI(api_key=api_key)

    response = client.embeddings.create(
        model="text-embedding-ada-002",
        input=text[:8000],
    )
    return response.data[0].embedding


def _fallback_embedding(text: str) -> list:
    """Generate a deterministic pseudo-random embedding based on text hash.

    This produces consistent embeddings for the same text, enabling
    meaningful (though not semantic) similarity comparisons.
    """
    # Use hash of text as seed for reproducibility
    seed = hash(text) % (2**32)
    rng = np.random.RandomState(seed)
    embedding = rng.randn(EMBEDDING_DIM).tolist()
    # Normalize
    norm = np.linalg.norm(embedding)
    if norm > 0:
        embedding = [x / norm for x in embedding]
    return embedding


def generate_and_store_embedding(meeting):
    """Generate embedding for a meeting and store it."""
    from analytics.models import MeetingEmbedding

    text = f"{meeting.transcript}\n\nSummary: {meeting.summary}"
    embedding = generate_embedding(text)

    MeetingEmbedding.objects.update_or_create(
        meeting=meeting,
        defaults={'embedding': embedding},
    )
    logger.info(f"Stored embedding for meeting {meeting.id}")
    return embedding


def cosine_similarity(vec1: list, vec2: list) -> float:
    """Compute cosine similarity between two vectors."""
    a = np.array(vec1)
    b = np.array(vec2)
    dot = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot / (norm_a * norm_b))
