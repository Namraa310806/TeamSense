import logging
from collections import defaultdict

from ai_engine.model_loader import ModelManager

logger = logging.getLogger(__name__)


class EmotionService:
    def __init__(self, model_name='j-hartmann/emotion-english-distilroberta-base'):
        self.model_name = model_name

    def analyze(self, text):
        if not text or not str(text).strip():
            return {'neutral': 1.0}

        try:
            classifier = ModelManager.get_emotion_pipeline()
            outputs = classifier(text, truncation=True)
            if outputs and isinstance(outputs[0], list):
                outputs = outputs[0]

            distribution = {}
            for row in outputs or []:
                label = str(row.get('label', 'neutral')).lower()
                score = float(row.get('score', 0.0))
                distribution[label] = round(score, 4)

            if not distribution:
                return {'neutral': 1.0}

            total = sum(distribution.values()) or 1.0
            normalized = {k: round(v / total, 4) for k, v in distribution.items()}
            return normalized
        except Exception as exc:
            logger.warning('Emotion analysis failed; returning neutral fallback: %s', exc)
            return {'neutral': 1.0}

    def aggregate(self, texts):
        bucket = defaultdict(float)
        count = 0
        for text in texts:
            result = self.analyze(text)
            for label, score in result.items():
                bucket[label] += float(score)
            count += 1

        if count == 0:
            return {'neutral': 1.0}

        return {k: round(v / count, 4) for k, v in bucket.items()}
