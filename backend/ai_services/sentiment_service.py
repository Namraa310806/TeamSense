"""
Sentiment Analysis Service using cardiffnlp/twitter-roberta-base-sentiment
"""
import logging

import torch
import numpy as np

from ai_engine.model_loader import ModelManager

logger = logging.getLogger(__name__)

class SentimentService:
    def __init__(self, model_name='distilbert-base-uncased-finetuned-sst-2-english'):
        self.model_name = model_name
        self.labels = ['negative', 'positive']

    def analyze(self, text):
        if not text or not str(text).strip():
            return {'label': 'neutral', 'scores': {'negative': 0.0, 'positive': 0.0, 'neutral': 1.0}}

        try:
            bundle = ModelManager.get_sentiment_bundle()
            tokenizer = bundle['tokenizer']
            model = bundle['model']
            labels = bundle['labels']

            inputs = tokenizer(text, return_tensors='pt', truncation=True)
            with torch.no_grad():
                logits = model(**inputs).logits
            scores = torch.softmax(logits, dim=1).numpy()[0]
            label_id = int(np.argmax(scores))
            positive = float(scores[labels.index('positive')])
            negative = float(scores[labels.index('negative')])

            return {
                'label': labels[label_id],
                'scores': {
                    'negative': negative,
                    'positive': positive,
                    'neutral': max(0.0, 1.0 - positive - negative),
                },
            }
        except Exception as exc:
            logger.warning('Sentiment analysis failed; returning safe neutral result: %s', exc)
            return {'label': 'neutral', 'scores': {'negative': 0.0, 'positive': 0.0, 'neutral': 1.0}}
