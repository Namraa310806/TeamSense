"""
HR AI Assistant Service using Mistral-7B-Instruct via Hugging Face Inference API
"""
import os
import requests
import logging

HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "")
logger = logging.getLogger(__name__)

SAFE_FALLBACK = "I am not supposed to answer this because relevant meeting content could not be extracted confidently."

class AssistantService:
    def __init__(self):
        self.api_url = HUGGINGFACE_API_URL
        self.headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"} if HUGGINGFACE_API_KEY else {}

    def ask(self, prompt, context=None, max_tokens=256):
        full_prompt = f"Context: {context}\n\nQuestion: {prompt}\nAnswer:"
        payload = {
            "inputs": full_prompt,
            "parameters": {"max_new_tokens": max_tokens}
        }
        try:
            response = requests.post(self.api_url, headers=self.headers, json=payload, timeout=45)
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and result:
                    return result[0].get("generated_text", SAFE_FALLBACK)
                if isinstance(result, dict) and "generated_text" in result:
                    return result["generated_text"]
                return SAFE_FALLBACK

            logger.warning("Assistant upstream returned %s: %s", response.status_code, response.text[:300])
            return SAFE_FALLBACK
        except Exception as exc:
            logger.warning("Assistant request failed: %s", exc)
            return SAFE_FALLBACK
