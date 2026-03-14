"""
Topic Extraction Service using lightweight frequency-based extraction
"""
import re
from collections import Counter


STOP_WORDS = {
    'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from', 'has', 'he',
    'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the', 'to', 'was', 'were', 'will',
    'with', 'this', 'they', 'their', 'them', 'or', 'if', 'but', 'about', 'into',
    'than', 'then', 'there', 'here', 'our', 'we', 'you', 'your', 'i', 'me', 'my',
    'so', 'do', 'does', 'did', 'have', 'had', 'having', 'can', 'could', 'should',
}


def _tokenize(text):
    return [t for t in re.findall(r"[a-zA-Z][a-zA-Z\-']+", text.lower()) if t not in STOP_WORDS]


def _ngrams(tokens, n):
    return [' '.join(tokens[i:i + n]) for i in range(len(tokens) - n + 1)]


class TopicService:
    def __init__(self, model_name='sentence-transformers/all-MiniLM-L6-v2'):
        # Keep signature for compatibility; lightweight extractor does not require model loading.
        self.model_name = model_name

    def extract_topics(self, text, top_n=5):
        if not text or len(text.strip()) == 0:
            return []

        tokens = _tokenize(text)
        if not tokens:
            return []

        candidates = []
        candidates.extend(tokens)
        candidates.extend(_ngrams(tokens, 2))
        candidates.extend(_ngrams(tokens, 3))

        scores = Counter(candidates)
        ranked = [phrase for phrase, _ in scores.most_common(max(top_n * 2, top_n))]

        unique = []
        seen = set()
        for phrase in ranked:
            if phrase not in seen:
                seen.add(phrase)
                unique.append(phrase)
            if len(unique) >= top_n:
                break
        return unique
