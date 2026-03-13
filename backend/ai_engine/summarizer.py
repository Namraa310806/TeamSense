"""Transcript summarization using OpenAI with extractive fallback."""
import os
import logging
import re

logger = logging.getLogger(__name__)


def summarize_transcript(transcript: str) -> str:
    """Summarize a meeting transcript.

    Uses OpenAI if API key is available, otherwise falls back to extractive summarization.
    """
    api_key = os.getenv('OPENAI_API_KEY', '')

    if api_key:
        try:
            return _summarize_with_openai(transcript, api_key)
        except Exception as e:
            logger.warning(f"OpenAI summarization failed, using fallback: {e}")

    return _extractive_summary(transcript)


def _summarize_with_openai(transcript: str, api_key: str) -> str:
    """Use OpenAI to generate a summary."""
    from openai import OpenAI
    client = OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an HR meeting assistant. Summarize the following meeting transcript "
                    "in 3-5 bullet points. Focus on key decisions, action items, employee concerns, "
                    "and career development topics."
                ),
            },
            {"role": "user", "content": transcript[:4000]},
        ],
        max_tokens=500,
        temperature=0.3,
    )
    return response.choices[0].message.content


def _extractive_summary(transcript: str) -> str:
    """Simple extractive summarization using sentence scoring."""
    # Clean and split into sentences
    sentences = re.split(r'[.!?]+', transcript)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]

    if not sentences:
        return "No meaningful content found in the transcript."

    # Score sentences by keyword relevance
    important_keywords = [
        'goal', 'concern', 'issue', 'plan', 'project', 'deadline', 'feedback',
        'performance', 'improvement', 'challenge', 'success', 'team', 'burnout',
        'workload', 'career', 'promotion', 'training', 'decision', 'action',
        'priority', 'milestone', 'review', 'satisfaction', 'engagement',
    ]

    scored = []
    for sentence in sentences:
        lower = sentence.lower()
        score = sum(1 for kw in important_keywords if kw in lower)
        # Prefer earlier sentences slightly
        scored.append((score, sentence))

    scored.sort(key=lambda x: x[0], reverse=True)
    top_sentences = scored[:5]

    summary_lines = [f"• {s[1].strip()}" for s in top_sentences]
    return "Key Points:\n" + "\n".join(summary_lines)
