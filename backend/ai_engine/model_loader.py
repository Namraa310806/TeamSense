import logging
import threading
from typing import Any, Dict, Optional

import torch
from transformers import AutoModel, AutoModelForSequenceClassification, AutoTokenizer, pipeline

logger = logging.getLogger(__name__)


class ModelManager:
    """Lazy global cache for expensive model objects."""

    _lock = threading.Lock()
    _cache: Dict[str, Any] = {}

    @classmethod
    def _get_or_create(cls, key: str, factory):
        if key in cls._cache:
            return cls._cache[key]
        with cls._lock:
            if key in cls._cache:
                return cls._cache[key]
            cls._cache[key] = factory()
            return cls._cache[key]

    @classmethod
    def get_whisper_pipeline(cls):
        def build():
            model_candidates = ['openai/whisper-small', 'openai/whisper-tiny.en']
            last_exc: Optional[Exception] = None
            for model_name in model_candidates:
                try:
                    logger.info('Loading ASR model: %s', model_name)
                    return pipeline(
                        task='automatic-speech-recognition',
                        model=model_name,
                        device=-1,
                    )
                except Exception as exc:
                    last_exc = exc
                    logger.warning('ASR model load failed for %s: %s', model_name, exc)
            raise RuntimeError(f'Unable to load ASR model: {last_exc}')

        return cls._get_or_create('asr_pipeline', build)

    @classmethod
    def get_sentiment_bundle(cls):
        def build():
            model_name = 'distilbert-base-uncased-finetuned-sst-2-english'
            logger.info('Loading sentiment model: %s', model_name)
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForSequenceClassification.from_pretrained(model_name)
            return {'tokenizer': tokenizer, 'model': model, 'labels': ['negative', 'positive']}

        return cls._get_or_create('sentiment_bundle', build)

    @classmethod
    def get_summarizer_pipeline(cls):
        def build():
            model_name = 'facebook/bart-large-cnn'
            logger.info('Loading summarization model: %s', model_name)
            return pipeline('summarization', model=model_name, device=-1)

        return cls._get_or_create('summarizer_pipeline', build)

    @classmethod
    def get_emotion_pipeline(cls):
        def build():
            model_name = 'j-hartmann/emotion-english-distilroberta-base'
            logger.info('Loading emotion model: %s', model_name)
            return pipeline('text-classification', model=model_name, top_k=None, device=-1)

        return cls._get_or_create('emotion_pipeline', build)

    @classmethod
    def get_embedding_bundle(cls):
        def build():
            model_name = 'sentence-transformers/all-MiniLM-L6-v2'
            logger.info('Loading embedding model: %s', model_name)
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModel.from_pretrained(model_name)
            model.eval()
            return {'tokenizer': tokenizer, 'model': model}

        return cls._get_or_create('embedding_bundle', build)


def mean_pool(last_hidden_state, attention_mask):
    mask = attention_mask.unsqueeze(-1).expand(last_hidden_state.size()).float()
    masked = last_hidden_state * mask
    summed = torch.sum(masked, dim=1)
    counts = torch.clamp(mask.sum(dim=1), min=1e-9)
    return summed / counts
