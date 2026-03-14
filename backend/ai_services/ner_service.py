"""
NER Service using dslim/bert-base-NER
"""
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline

class NERService:
    def __init__(self, model_name='dslim/bert-base-NER'):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForTokenClassification.from_pretrained(model_name)
        self.ner_pipeline = pipeline('ner', model=self.model, tokenizer=self.tokenizer, aggregation_strategy="simple")

    def extract_entities(self, text):
        if not text or len(text.strip()) == 0:
            return []
        entities = self.ner_pipeline(text)
        # Return unique entities with their type
        return list({(e['entity_group'], e['word']) for e in entities})
