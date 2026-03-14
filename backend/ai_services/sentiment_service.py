"""
Sentiment Analysis Service using cardiffnlp/twitter-roberta-base-sentiment
"""
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import numpy as np

class SentimentService:
    def __init__(self, model_name='cardiffnlp/twitter-roberta-base-sentiment'):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
        self.labels = ['negative', 'neutral', 'positive']

    def analyze(self, text):
        inputs = self.tokenizer(text, return_tensors='pt', truncation=True)
        with torch.no_grad():
            logits = self.model(**inputs).logits
        scores = torch.softmax(logits, dim=1).numpy()[0]
        label_id = int(np.argmax(scores))
        return {
            'label': self.labels[label_id],
            'scores': {self.labels[i]: float(scores[i]) for i in range(len(self.labels))}
        }
