"""
Summarization Service using facebook/bart-large-cnn
"""
import logging

from ai_engine.model_loader import ModelManager

logger = logging.getLogger(__name__)

class SummarizationService:
    def __init__(self, model_name='facebook/bart-large-cnn'):
        self.model_name = model_name

    def summarize(self, text, min_length=30, max_length=130):
        if not text or len(text.strip()) == 0:
            return ''
        try:
            summarizer = ModelManager.get_summarizer_pipeline()
            summary = summarizer(text, min_length=min_length, max_length=max_length, truncation=True)
            return summary[0]['summary_text'] if summary else ''
        except Exception as exc:
            logger.warning('Summarization failed; using extractive fallback: %s', exc)
            # Safe fallback: first 2 meaningful sentences.
            segments = [s.strip() for s in text.replace('\n', ' ').split('.') if len(s.strip()) > 20]
            return '. '.join(segments[:2]).strip() + ('.' if segments else '')
