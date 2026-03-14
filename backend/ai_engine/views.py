from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from ai_services.embedding_service import EmbeddingService
from ai_services.vector_store import FaissVectorStore
from ai_services.assistant_service import AssistantService
from employees.models import Employee
from meetings.models import Meeting
from analytics.models import EmployeeInsight, MeetingAnalysis

SAFE_REFUSAL = "I am not supposed to answer this because relevant meeting content could not be extracted confidently."

@api_view(['POST'])
def ai_query(request):
    """RAG-based AI query endpoint.

    Input:
        query: str - the question to ask
        employee_id: int (optional) - filter to specific employee
    """
    query = request.data.get('query', '')
    employee_id = request.data.get('employee_id')

    if not query:
        return Response({'error': 'Query is required'}, status=status.HTTP_400_BAD_REQUEST)

    from .rag import rag_query
    result = rag_query(query, employee_id=employee_id)

    return Response(result)

@api_view(['POST'])
def hr_assistant(request):
    """HR AI Assistant endpoint using Mistral-7B-Instruct (Hugging Face API)."""
    question = request.data.get('question', '')
    employee_id = request.data.get('employee_id')
    if not question:
        return Response({'error': 'Question is required'}, status=status.HTTP_400_BAD_REQUEST)
    # Gather context (simple demo: summaries, feedback, sentiment)
    context_parts = []
    if employee_id:
        try:
            emp = Employee.objects.get(id=employee_id)
            context_parts.append(f"Employee: {emp.name}, Dept: {emp.department}, Role: {emp.role}")
            meetings = Meeting.objects.filter(employee=emp).order_by('-date')[:8]
            for m in meetings:
                context_parts.append(
                    f"Meeting {m.id} on {m.date}: summary={m.summary or 'N/A'}; sentiment={m.sentiment_score}"
                )

                analysis = MeetingAnalysis.objects.filter(meeting=m).first()
                if analysis:
                    context_parts.append(
                        "Analysis signals: "
                        f"engagement={analysis.engagement_signals}; "
                        f"conflict={analysis.conflict_detection}; "
                        f"participation_score={analysis.participation_score}"
                    )
        except Employee.DoesNotExist:
            pass
        try:
            insight = EmployeeInsight.objects.get(employee_id=employee_id)
            context_parts.append(
                f"Employee insights: concerns={insight.concerns}; strengths={insight.strengths}; "
                f"career_goals={insight.career_goals}; burnout_risk={insight.burnout_risk}"
            )
        except EmployeeInsight.DoesNotExist:
            pass
    else:
        # General context: last 5 meeting summaries
        for m in Meeting.objects.order_by('-date')[:10]:
            context_parts.append(
                f"Meeting {m.id} with {m.employee.name} on {m.date}: summary={m.summary or 'N/A'}; sentiment={m.sentiment_score}"
            )

    if len(context_parts) < 2:
        return Response({'answer': SAFE_REFUSAL})

    context = '\n'.join(part for part in context_parts if part and str(part).strip())
    assistant = AssistantService()
    grounded_question = (
        f"{question}\n\n"
        "Instruction: respond only from the provided context. "
        f"If context is unrelated or weak, respond exactly with: {SAFE_REFUSAL}"
    )
    answer = assistant.ask(grounded_question, context=context)
    return Response({'answer': answer})

# Example: 384 for all-MiniLM-L6-v2
EMBEDDING_DIM = 384
VECTOR_INDEX_PATH = 'faiss.index'
META_PATH = 'faiss_meta.pkl'

_embedding_service = None
_vector_store = None


def _get_embedding_service():
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service


def _get_vector_store():
    global _vector_store
    if _vector_store is None:
        _vector_store = FaissVectorStore(
            dim=EMBEDDING_DIM,
            index_path=VECTOR_INDEX_PATH,
            meta_path=META_PATH,
        )
    return _vector_store

class SemanticSearchAPI(APIView):
    def post(self, request):
        query = request.data.get('query')
        if not query:
            return Response({'error': 'Query is required.'}, status=status.HTTP_400_BAD_REQUEST)
        embedding_service = _get_embedding_service()
        vector_store = _get_vector_store()
        query_vec = embedding_service.embed_text(query)
        results = vector_store.search(query_vec, top_k=5)
        # Add type and reference info to each result
        return Response({'results': results})
