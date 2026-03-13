"""Sentiment analysis using TextBlob (local, no API key needed)."""
import logging

logger = logging.getLogger(__name__)


def analyze_sentiment(text: str) -> float:
    """Analyze sentiment of text.

    Returns a float between -1.0 (very negative) and 1.0 (very positive).
    Uses TextBlob for local inference.
    """
    try:
        from textblob import TextBlob
        blob = TextBlob(text)

        # TextBlob polarity is already in [-1, 1]
        polarity = blob.sentiment.polarity

        # Normalize to [0, 1] for easier display
        normalized = (polarity + 1) / 2

        return round(normalized, 3)
    except Exception as e:
        logger.warning(f"Sentiment analysis failed: {e}")
        return 0.5  # Neutral fallback


def get_emotion_breakdown(text: str) -> dict:
    """Get a breakdown of emotions detected in text."""
    emotion_keywords = {
        'positive': ['happy', 'excited', 'great', 'excellent', 'good', 'love', 'amazing',
                      'wonderful', 'fantastic', 'proud', 'grateful', 'optimistic', 'confident'],
        'negative': ['frustrated', 'worried', 'concerned', 'stressed', 'tired', 'overwhelmed',
                      'disappointed', 'unhappy', 'angry', 'burnout', 'difficult', 'problem'],
        'neutral': ['okay', 'fine', 'normal', 'regular', 'standard', 'usual', 'typical'],
    }

    text_lower = text.lower()
    counts = {}
    total = 0

    for emotion, keywords in emotion_keywords.items():
        count = sum(text_lower.count(kw) for kw in keywords)
        counts[emotion] = count
        total += count

    if total == 0:
        return {'positive': 0.33, 'negative': 0.33, 'neutral': 0.34}

    return {emotion: round(count / total, 2) for emotion, count in counts.items()}
