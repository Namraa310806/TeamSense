"""
HR AI Assistant Service using Mistral-7B-Instruct via Hugging Face Inference API
"""
import os
import requests

HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "")

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
        response = requests.post(self.api_url, headers=self.headers, json=payload)
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and result:
                return result[0].get("generated_text", "")
            elif isinstance(result, dict) and "generated_text" in result:
                return result["generated_text"]
        return f"[Error] {response.status_code}: {response.text}"
