from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
import logging
from ai_services.embedding_service import EmbeddingService
from ai_services.vector_store import FaissVectorStore
from ai_services.assistant_service import AssistantService
from employees.models import Employee
from meetings.models import Meeting
from analytics.models import EmployeeInsight, MeetingAnalysis

SAFE_REFUSAL = "I am not supposed to answer this because relevant meeting content could not be extracted confidently."
logger = logging.getLogger(__name__)


def _is_admin(user):
    return hasattr(user, 'profile') and user.profile.role == 'ADMIN'


def _user_org(user):
    if hasattr(user, 'profile'):
        return user.profile.organization
    return None


def _build_hr_context(request_user, employee_id=None, organization_id=None):
    org = _user_org(request_user)

    if organization_id is not None:
        try:
            organization_id = int(organization_id)
        except (TypeError, ValueError):
            raise ValueError('organization_id must be an integer')

        if not _is_admin(request_user):
            if org is None or org.id != organization_id:
                raise PermissionError('You can only query data from your own organization.')

    scoped_org_id = organization_id if organization_id is not None else (org.id if org else None)

    context_parts = []
    if employee_id:
        employee_qs = Employee.objects.filter(id=employee_id)
        if scoped_org_id is not None:
            employee_qs = employee_qs.filter(organization_id=scoped_org_id)

        emp = employee_qs.first()
        if not emp:
            return []

        context_parts.append(f"Employee: {emp.name}, Dept: {emp.department}, Role: {emp.role}")

        meetings_qs = Meeting.objects.filter(employee=emp)
        if scoped_org_id is not None:
            meetings_qs = meetings_qs.filter(organization_id=scoped_org_id)
        meetings = meetings_qs.order_by('-date')[:8]

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

        insight = EmployeeInsight.objects.filter(employee_id=employee_id).first()
        if insight:
            context_parts.append(
                f"Employee insights: concerns={insight.concerns}; strengths={insight.strengths}; "
                f"career_goals={insight.career_goals}; burnout_risk={insight.burnout_risk}"
            )
        return context_parts

    meetings_qs = Meeting.objects.select_related('employee').all()
    if scoped_org_id is not None:
        meetings_qs = meetings_qs.filter(organization_id=scoped_org_id)
    meetings = meetings_qs.order_by('-date')[:10]

    for m in meetings:
        context_parts.append(
            f"Meeting {m.id} with {m.employee.name} on {m.date}: summary={m.summary or 'N/A'}; sentiment={m.sentiment_score}"
        )

    return context_parts

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
@permission_classes([IsAuthenticated])
def hr_assistant(request):
    """HR AI Assistant endpoint using existing assistant service."""
    question = request.data.get('question', '') or request.data.get('query', '')
    employee_id = request.data.get('employee_id')
    organization_id = request.data.get('organization_id')
    if not question:
        return Response({'error': 'Question is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        context_parts = _build_hr_context(request.user, employee_id=employee_id, organization_id=organization_id)
    except PermissionError as exc:
        return Response({'error': str(exc)}, status=status.HTTP_403_FORBIDDEN)
    except ValueError as exc:
        return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def hr_ai_assistant_api(request):
    """Contract endpoint for floating widget.

    POST /api/hr-assistant/query/
    body: {"message": "...", "organization_id": "...", "user_id": "..."}
    returns: {"response": "..."}
    """
    message = request.data.get('message', '') or request.data.get('query', '') or request.data.get('question', '')
    organization_id = request.data.get('organization_id')
    employee_id = request.data.get('employee_id')

    if not message:
        return Response({'error': 'message is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        context_parts = _build_hr_context(request.user, employee_id=employee_id, organization_id=organization_id)
    except PermissionError as exc:
        return Response({'error': str(exc)}, status=status.HTTP_403_FORBIDDEN)
    except ValueError as exc:
        return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    if len(context_parts) < 2:
        return Response({'response': SAFE_REFUSAL})

    context = '\n'.join(part for part in context_parts if part and str(part).strip())
    assistant = AssistantService()
    grounded_question = (
        f"{message}\n\n"
        "Instruction: respond only from the provided HR context. "
        f"If context is unrelated or weak, respond exactly with: {SAFE_REFUSAL}"
    )
    answer = assistant.ask(grounded_question, context=context)
    return Response({'response': answer, 'answer': answer})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def test_openai(request):
    """Connectivity probe for OpenAI API with safe diagnostics."""
    assistant = AssistantService()
    ok, code, sample = assistant.test_connection()

    if ok:
        return Response(
            {
                'status': 'ok',
                'provider': 'openai',
                'message': 'OpenAI connection verified.',
                'sample_response': sample,
            },
            status=status.HTTP_200_OK,
        )

    error_status = status.HTTP_401_UNAUTHORIZED if code == 'invalid_api_key' else status.HTTP_503_SERVICE_UNAVAILABLE
    logger.warning('openai_connectivity_failed code=%s user_id=%s', code, getattr(request.user, 'id', None))
    return Response(
        {
            'status': 'error',
            'provider': 'openai',
            'code': code,
            'message': 'OpenAI connectivity check failed. Verify OPENAI_API_KEY configuration.',
        },
        status=error_status,
    )

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
