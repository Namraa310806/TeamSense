"""RAG (Retrieval-Augmented Generation) pipeline."""
import os
import logging
import re

logger = logging.getLogger(__name__)

SAFE_REFUSAL = "I am not supposed to answer this because relevant meeting content could not be extracted confidently."
MIN_VECTOR_CONFIDENCE = 0.18
MIN_QUERY_TERM_OVERLAP = 2


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-zA-Z0-9_]+", (text or '').lower()))


def _context_quality_gate(query: str, context_parts: list[str], top_similarity: float) -> bool:
    if top_similarity < MIN_VECTOR_CONFIDENCE:
        return False

    query_terms = _tokenize(query)
    if not query_terms:
        return False

    context_terms = _tokenize("\n".join(context_parts))
    overlap = len(query_terms & context_terms)
    return overlap >= MIN_QUERY_TERM_OVERLAP


def rag_query(query: str, employee_id: int = None) -> dict:
    """Execute a RAG query against stored meeting transcripts.

    1. Convert query to embedding
    2. Vector similarity search across meeting embeddings
    3. Retrieve top relevant transcripts
    4. Generate answer using LLM with context
    """
    from .embeddings import generate_embedding, cosine_similarity
    from analytics.models import MeetingEmbedding
    from meetings.models import Meeting

    # Step 1: Generate query embedding
    query_embedding = generate_embedding(query)

    # Step 2: Vector similarity search
    embeddings = MeetingEmbedding.objects.select_related('meeting', 'meeting__employee').all()
    if employee_id:
        embeddings = embeddings.filter(meeting__employee_id=employee_id)

    scored = []
    for emb_record in embeddings:
        if emb_record.embedding:
            similarity = cosine_similarity(query_embedding, emb_record.embedding)
            scored.append((similarity, emb_record))

    # Sort by similarity (descending)
    scored.sort(key=lambda x: x[0], reverse=True)

    # Step 3: Get top 3 relevant transcripts
    top_k = scored[:3]
    if not top_k:
        return {
            'answer': SAFE_REFUSAL,
            'sources': [],
            'confidence': 0.0,
        }

    # Build context from top matches
    context_parts = []
    sources = []
    for similarity, emb_record in top_k:
        meeting = emb_record.meeting
        context_parts.append(
            f"Meeting with {meeting.employee.name} on {meeting.date}:\n"
            f"Summary: {meeting.summary or 'N/A'}\n"
            f"Transcript excerpt: {meeting.transcript[:500]}\n"
        )
        sources.append({
            'meeting_id': meeting.id,
            'employee_name': meeting.employee.name,
            'date': meeting.date.isoformat(),
            'similarity': round(similarity, 3),
        })

    context = "\n---\n".join(context_parts)
    top_confidence = float(top_k[0][0]) if top_k else 0.0

    if not _context_quality_gate(query, context_parts, top_confidence):
        return {
            'answer': SAFE_REFUSAL,
            'sources': sources,
            'confidence': round(top_confidence, 3),
        }

    # Step 4: Generate answer
    answer = _generate_answer(query, context)

    return {
        'answer': answer,
        'sources': sources,
        'confidence': round(top_confidence, 3),
    }


def _generate_answer(query: str, context: str) -> str:
    """Generate an answer using LLM or fallback."""
    api_key = os.getenv('OPENAI_API_KEY', '')

    if api_key:
        try:
            return _openai_answer(query, context, api_key)
        except Exception as e:
            logger.warning(f"OpenAI RAG answer failed, using fallback: {e}")

    return _fallback_answer(query, context)


def _openai_answer(query: str, context: str, api_key: str) -> str:
    """Use OpenAI to generate an answer from context."""
    from openai import OpenAI
    client = OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an AI HR assistant. Use ONLY the provided context and do not invent facts. "
                    "Provide concise, relevant answers tied to employee names and dates when available. "
                    "If context is insufficient or unrelated, respond exactly with: "
                    "'I am not supposed to answer this because relevant meeting content could not be extracted confidently.'"
                ),
            },
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {query}",
            },
        ],
        max_tokens=500,
        temperature=0.3,
    )
    return response.choices[0].message.content


def _fallback_answer(query: str, context: str) -> str:
    """Generate a simple answer by extracting relevant sentences from context."""
    query_words = _tokenize(query)
    context_lines = context.split('\n')

    relevant = []
    for line in context_lines:
        line_words = _tokenize(line)
        overlap = query_words & line_words
        if len(overlap) >= MIN_QUERY_TERM_OVERLAP and len(line.strip()) > 20:
            relevant.append(line.strip())

    if relevant:
        answer = "Based on meeting records:\n\n"
        for line in relevant[:5]:
            answer += f"• {line}\n"
        return answer

    return SAFE_REFUSAL
