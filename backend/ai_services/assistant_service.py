"""HR AI Assistant Service.

Primary path: local open-source Hugging Face model (auto-download on first use).
Fallback path: Hugging Face Inference API (if API key is configured).
Final path: extractive context-based answer.
"""
import os
import requests
import logging
import re

from transformers import pipeline

logger = logging.getLogger(__name__)

SAFE_FALLBACK = "I am not supposed to answer this because relevant meeting content could not be extracted confidently."
DEFAULT_LOCAL_MODEL = os.getenv('ASSISTANT_LOCAL_MODEL', 'google/flan-t5-base')
HF_API_MODEL = os.getenv('ASSISTANT_HF_API_MODEL', 'mistralai/Mistral-7B-Instruct-v0.2')
HUGGINGFACE_API_KEY = os.getenv('HUGGINGFACE_API_KEY', '')


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-zA-Z0-9_]+", (text or '').lower()))


def _extractive_fallback(question: str, context: str) -> str:
    query_terms = _tokenize(question)
    lines = [line.strip() for line in context.split('\n') if line.strip()]

    scored = []
    for line in lines:
        overlap = len(query_terms & _tokenize(line))
        if overlap > 0 and len(line) > 24:
            scored.append((overlap, line))

    if not scored:
        return SAFE_FALLBACK

    scored.sort(key=lambda x: x[0], reverse=True)
    bullets = '\n'.join(f"- {line}" for _, line in scored[:5])
    return f"Based on available records:\n{bullets}"

class AssistantService:
    _local_pipeline = None

    def __init__(self):
        self.api_url = f"https://api-inference.huggingface.co/models/{HF_API_MODEL}"
        self.headers = {'Authorization': f'Bearer {HUGGINGFACE_API_KEY}'} if HUGGINGFACE_API_KEY else {}

    @classmethod
    def _get_local_pipeline(cls):
        if cls._local_pipeline is None:
            logger.info('Loading local assistant model: %s', DEFAULT_LOCAL_MODEL)
            cls._local_pipeline = pipeline(
                'text2text-generation',
                model=DEFAULT_LOCAL_MODEL,
                tokenizer=DEFAULT_LOCAL_MODEL,
                device=-1,
            )
        return cls._local_pipeline

    def _ask_local(self, prompt: str, context: str, max_tokens: int) -> str:
        generator = self._get_local_pipeline()
        # Keep prompt compact for small open-source models.
        compact_context = (context or '')[:2800]
        full_prompt = (
            "You are an HR assistant. Use only the context below. "
            f"If not enough evidence, answer exactly: {SAFE_FALLBACK}\n\n"
            f"Context:\n{compact_context}\n\n"
            f"Question:\n{prompt}\n\n"
            "Answer:"
        )
        output = generator(full_prompt, max_new_tokens=max_tokens, do_sample=False)
        if isinstance(output, list) and output:
            text = output[0].get('generated_text', '').strip()
            return text or SAFE_FALLBACK
        return SAFE_FALLBACK

    def _ask_hf_api(self, prompt: str, context: str, max_tokens: int) -> str:
        full_prompt = f"Context: {context[:3500]}\n\nQuestion: {prompt}\nAnswer:"
        payload = {
            'inputs': full_prompt,
            'parameters': {'max_new_tokens': max_tokens},
        }
        response = requests.post(self.api_url, headers=self.headers, json=payload, timeout=45)
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and result:
                return result[0].get('generated_text', SAFE_FALLBACK) or SAFE_FALLBACK
            if isinstance(result, dict) and 'generated_text' in result:
                return result['generated_text'] or SAFE_FALLBACK
            return SAFE_FALLBACK
        raise RuntimeError(f'Assistant upstream returned {response.status_code}: {response.text[:240]}')

    def ask(self, prompt, context=None, max_tokens=256):
        context = context or ''

        # 1) Local open-source model (preferred for hackathon reliability)
        try:
            answer = self._ask_local(prompt, context, max_tokens)
            if answer and answer.strip():
                return answer.strip()
        except Exception as exc:
            logger.warning('Local assistant model failed: %s', exc)

        # 2) Optional HF hosted API if key is available
        if self.headers:
            try:
                answer = self._ask_hf_api(prompt, context, max_tokens)
                if answer and answer.strip():
                    return answer.strip()
            except Exception as exc:
                logger.warning('Hosted assistant fallback failed: %s', exc)

        # 3) Guaranteed non-crashing extractive fallback
        return _extractive_fallback(prompt, context)
