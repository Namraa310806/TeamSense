"""
Summarization Service using facebook/bart-large-cnn
"""
from transformers import pipeline

class SummarizationService:
    def __init__(self, model_name='facebook/bart-large-cnn'):
        self.summarizer = pipeline('summarization', model=model_name)

    def summarize(self, text, min_length=30, max_length=130):
        if not text or len(text.strip()) == 0:
            return ''
        summary = self.summarizer(text, min_length=min_length, max_length=max_length, truncation=True)
        return summary[0]['summary_text'] if summary else ''
