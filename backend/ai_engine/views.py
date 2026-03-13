from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from ai_services.embedding_service import EmbeddingService
from ai_services.vector_store import FaissVectorStore
from ai_services.assistant_service import AssistantService
from employees.models import Employee
from meetings.models import Meeting
from analytics.models import EmployeeInsight

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
            meetings = Meeting.objects.filter(employee=emp)
            for m in meetings:
                context_parts.append(f"Meeting summary: {m.summary}")
                context_parts.append(f"Sentiment: {m.sentiment_score}")
        except Employee.DoesNotExist:
            pass
        try:
            insight = EmployeeInsight.objects.get(employee_id=employee_id)
            context_parts.append(f"Insights: {insight.concerns}, Burnout risk: {insight.burnout_risk}")
        except EmployeeInsight.DoesNotExist:
            pass
    else:
        # General context: last 5 meeting summaries
        for m in Meeting.objects.order_by('-date')[:5]:
            context_parts.append(f"Meeting summary: {m.summary}")
    context = '\n'.join(context_parts)
    assistant = AssistantService()
    answer = assistant.ask(question, context=context)
    return Response({'answer': answer})

from ai_services.embedding_service import EmbeddingService
from ai_services.vector_store import FaissVectorStore
from rest_framework.views import APIView

# Example: 384 for all-MiniLM-L6-v2
EMBEDDING_DIM = 384
VECTOR_INDEX_PATH = 'faiss.index'
META_PATH = 'faiss_meta.pkl'

embedding_service = EmbeddingService()
vector_store = FaissVectorStore(dim=EMBEDDING_DIM, index_path=VECTOR_INDEX_PATH, meta_path=META_PATH)

class SemanticSearchAPI(APIView):
    def post(self, request):
        query = request.data.get('query')
        if not query:
            return Response({'error': 'Query is required.'}, status=status.HTTP_400_BAD_REQUEST)
        query_vec = embedding_service.embed_text(query)
        results = vector_store.search(query_vec, top_k=5)
        return Response({'results': results})
