"""
Topic Extraction Service using KeyBERT and MiniLM
"""
from keybert import KeyBERT

class TopicService:
    def __init__(self, model_name='sentence-transformers/all-MiniLM-L6-v2'):
        self.kw_model = KeyBERT(model_name)

    def extract_topics(self, text, top_n=5):
        if not text or len(text.strip()) == 0:
            return []
        keywords = self.kw_model.extract_keywords(text, keyphrase_ngram_range=(1, 3), stop_words='english', top_n=top_n)
        return [kw[0] for kw in keywords]
