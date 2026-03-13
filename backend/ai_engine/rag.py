"""RAG (Retrieval-Augmented Generation) pipeline."""
import os
import logging

logger = logging.getLogger(__name__)


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
            'answer': 'No relevant meeting transcripts found. Please upload some meeting transcripts first.',
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

    # Step 4: Generate answer
    answer = _generate_answer(query, context)

    return {
        'answer': answer,
        'sources': sources,
        'confidence': round(top_k[0][0], 3) if top_k else 0.0,
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
                    "You are an AI HR assistant. Answer questions about employees based on "
                    "the provided meeting transcript context. Be specific, cite dates and "
                    "employee names. If the context doesn't contain enough information, say so."
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
    query_words = set(query.lower().split())
    context_lines = context.split('\n')

    relevant = []
    for line in context_lines:
        line_words = set(line.lower().split())
        overlap = query_words & line_words
        if len(overlap) >= 2 and len(line.strip()) > 20:
            relevant.append(line.strip())

    if relevant:
        answer = "Based on meeting records:\n\n"
        for line in relevant[:5]:
            answer += f"• {line}\n"
        return answer

    return (
        "Based on the available meeting transcripts, I found related discussions. "
        f"The context includes the following information:\n\n{context[:800]}"
    )
