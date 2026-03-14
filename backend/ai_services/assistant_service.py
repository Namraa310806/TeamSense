"""HR AI Assistant Service using OpenAI as primary reasoning engine."""
import os
import logging
import re
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from openai import OpenAI, AuthenticationError, OpenAIError

logger = logging.getLogger(__name__)

SAFE_FALLBACK = "I am not supposed to answer this because relevant meeting content could not be extracted confidently."
OPENAI_MODEL = os.getenv('ASSISTANT_OPENAI_MODEL', 'gpt-4o-mini')


def _mask_secret(value: str) -> str:
    if not value:
        return 'missing'
    if len(value) <= 10:
        return '***masked***'
    return f"{value[:7]}...{value[-4:]}"


def _resolve_openai_api_key() -> str:
    try:
        return (getattr(settings, 'OPENAI_API_KEY', '') or os.getenv('OPENAI_API_KEY', '')).strip()
    except ImproperlyConfigured:
        return os.getenv('OPENAI_API_KEY', '').strip()


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-zA-Z0-9_]+", (text or '').lower()))


def _to_float(value, default=None):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _extract_profiles(context: str):
    """Parse lightweight employee profile hints from context text."""
    profiles = {}
    lines = [line.strip() for line in context.split('\n') if line.strip()]

    meeting_re = re.compile(
        r"Meeting\s+\d+\s+with\s+(.+?)\s+on\s+([^:]+):\s+summary=(.*?);\s*sentiment=([-+]?[0-9]*\.?[0-9]+|None)",
        re.IGNORECASE,
    )
    employee_re = re.compile(r"Employee:\s*(.+?),\s*Dept:\s*(.*?),\s*Role:\s*(.*)$", re.IGNORECASE)
    risk_re = re.compile(r"burnout_risk=([-+]?[0-9]*\.?[0-9]+)", re.IGNORECASE)

    for line in lines:
        m = meeting_re.search(line)
        if m:
            name = m.group(1).strip()
            sentiment = _to_float(m.group(4))
            profile = profiles.setdefault(name, {'sentiments': [], 'summaries': [], 'burnout_risk': None})
            if sentiment is not None:
                profile['sentiments'].append(sentiment)
            summary = (m.group(3) or '').strip()
            if summary and summary != 'N/A':
                profile['summaries'].append(summary)
            continue

        em = employee_re.search(line)
        if em:
            name = em.group(1).strip()
            profile = profiles.setdefault(name, {'sentiments': [], 'summaries': [], 'burnout_risk': None})
            profile['department'] = em.group(2).strip()
            profile['role'] = em.group(3).strip()

        if 'Employee insights:' in line:
            rm = risk_re.search(line)
            if rm and profiles:
                # apply to last known profile in single-employee context
                last_name = next(reversed(profiles))
                profiles[last_name]['burnout_risk'] = _to_float(rm.group(1))

    # derive averages
    for profile in profiles.values():
        sentiments = profile.get('sentiments', [])
        profile['avg_sentiment'] = (sum(sentiments) / len(sentiments)) if sentiments else None

    return profiles


def _rule_based_answer(question: str, context: str) -> str:
    q = (question or '').lower()
    profiles = _extract_profiles(context)
    if not profiles:
        return ''

    rows = [(name, data) for name, data in profiles.items()]

    # Intent: negative sentiment
    if any(term in q for term in ['negative sentiment', 'low sentiment', 'unhappy', 'declining sentiment']):
        at_risk = [(n, d) for n, d in rows if d.get('avg_sentiment') is not None and d['avg_sentiment'] < 0.45]
        if at_risk:
            names = ', '.join(f"{n} ({d['avg_sentiment']:.2f})" for n, d in at_risk[:5])
            return f"Employees showing lower sentiment: {names}. Recommended action: schedule focused check-ins and review workload blockers."
        return "No employees currently show strong negative sentiment in the available records."

    # Intent: attrition/burnout risk
    if any(term in q for term in ['attrition', 'burnout', 'risk']):
        risk_rows = [(n, d) for n, d in rows if d.get('burnout_risk') is not None]
        risk_rows.sort(key=lambda x: x[1]['burnout_risk'], reverse=True)
        if risk_rows:
            top = ', '.join(f"{n} ({d['burnout_risk']:.2f})" for n, d in risk_rows[:5])
            return f"Highest burnout/attrition indicators: {top}. Recommended action: manager 1:1s, priority reset, and workload balancing."
        return "Burnout risk indicators are not present in the current context."

    # Intent: summarize meetings
    if any(term in q for term in ['summarize', 'summary', 'meeting']):
        snippets = []
        for name, data in rows:
            for s in data.get('summaries', [])[:1]:
                snippets.append(f"{name}: {s}")
        if snippets:
            return "Recent meeting highlights:\n- " + "\n- ".join(snippets[:5])
        return "Meeting summaries are limited in the current context."

    # Intent: engagement issues by sentiment proxy
    if any(term in q for term in ['engagement', 'team sentiment', 'team', 'issues']):
        weak = [(n, d) for n, d in rows if d.get('avg_sentiment') is not None and d['avg_sentiment'] < 0.5]
        if weak:
            names = ', '.join(n for n, _ in weak[:5])
            return f"Potential engagement concerns are visible for: {names}. Recommended action: follow up on blockers and clarify next-step ownership."
        return "Engagement signals appear stable based on available sentiment records."

    # Generic concise answer using top profile facts.
    ordered = sorted(rows, key=lambda x: (x[1].get('avg_sentiment') is None, x[1].get('avg_sentiment') or 0.0))
    sample = ', '.join(
        f"{name} (sentiment {data['avg_sentiment']:.2f})"
        for name, data in ordered[:5]
        if data.get('avg_sentiment') is not None
    )
    if sample:
        return f"Based on current HR records: {sample}. Ask for sentiment, risk, or meeting summary for a more targeted view."

    return ''


def _extractive_fallback(question: str, context: str) -> str:
    rule_answer = _rule_based_answer(question, context)
    if rule_answer:
        return rule_answer

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
    def __init__(self):
        self.api_key = _resolve_openai_api_key()
        self.model = os.getenv('ASSISTANT_OPENAI_MODEL', OPENAI_MODEL)
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None
        logger.info('assistant_service_init openai_key=%s model=%s', _mask_secret(self.api_key), self.model)

    def _ask_openai(self, prompt: str, context: str, max_tokens: int) -> str:
        if not self.api_key or not self.client:
            raise RuntimeError('OPENAI_API_KEY is not configured')
        compact_context = (context or '')[:7000]
        logger.info('openai_request_start model=%s prompt_chars=%d context_chars=%d', self.model, len(prompt or ''), len(compact_context))
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    'role': 'system',
                    'content': (
                        'You are an intelligent HR analytics assistant. '
                        'Use only provided context and do not fabricate facts. '
                        f'If evidence is weak, respond exactly with: {SAFE_FALLBACK}'
                    ),
                },
                {
                    'role': 'user',
                    'content': (
                        f'Context:\n{compact_context}\n\n'
                        f'Question:\n{prompt}\n\n'
                        'Respond concisely with key insight and short recommendation.'
                    ),
                },
            ],
            max_tokens=max_tokens,
            temperature=0.2,
        )
        logger.info('openai_response_received model=%s choices=%d', self.model, len(response.choices or []))
        return (response.choices[0].message.content or '').strip() or SAFE_FALLBACK

    def test_connection(self):
        if not self.api_key or not self.client:
            return False, 'OPENAI_API_KEY not found', None

        try:
            logger.info('openai_test_request_start model=%s', self.model)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {'role': 'system', 'content': 'You are a connectivity test assistant.'},
                    {'role': 'user', 'content': 'Reply with exactly: OK'},
                ],
                max_tokens=8,
                temperature=0,
            )
            content = (response.choices[0].message.content or '').strip()
            logger.info('openai_test_response_received model=%s', self.model)
            return True, 'ok', content
        except AuthenticationError as exc:
            logger.error('openai_test_auth_failed error=%s', str(exc))
            return False, 'invalid_api_key', None
        except OpenAIError as exc:
            logger.error('openai_test_openai_error error=%s', str(exc))
            return False, 'openai_error', None
        except Exception as exc:
            logger.exception('openai_test_unexpected_error')
            return False, f'unexpected_error: {exc.__class__.__name__}', None

    def ask(self, prompt, context=None, max_tokens=256):
        context = context or ''

        # 1) OpenAI generation path
        try:
            answer = self._ask_openai(prompt, context, max_tokens)
            if answer and answer.strip():
                return answer.strip()
        except AuthenticationError as exc:
            logger.error('openai_auth_failed error=%s', str(exc))
        except Exception as exc:
            logger.warning('OpenAI assistant generation failed: %s', exc)

        # 2) Guaranteed non-crashing extractive fallback
        return _extractive_fallback(prompt, context)
