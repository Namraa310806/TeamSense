import uuid

from django.core.files.storage import default_storage
from django.db.models import Avg
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.permissions import IsAdmin, IsCHR, IsExecutive, IsHR
from analytics.models import SentimentInsight
from employees.models import Employee
from meetings.models import Meeting

from .models import Feedback, IngestionJob
from .serializers import (
    FeedbackSerializer,
    FormsIngestSerializer,
    IngestionJobSerializer,
    SlackIngestSerializer,
)
from .tasks import (
    ingest_document_task,
    ingest_google_forms_task,
    ingest_slack_messages_task,
    parse_csv_task,
)


def _user_org(user):
    if hasattr(user, 'profile'):
        return user.profile.organization
    return None


def _is_admin(user):
    return hasattr(user, 'profile') and user.profile.role == 'ADMIN'


def _scope_queryset_for_user(queryset, request_user, organization_field='organization'):
    if _is_admin(request_user):
        return queryset
    org = _user_org(request_user)
    if org is None:
        return queryset
    return queryset.filter(**{organization_field: org})


def _create_job(source, request, metadata=None):
    return IngestionJob.objects.create(
        source=source,
        status=IngestionJob.STATUS_QUEUED,
        created_by=request.user,
        metadata=metadata or {},
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsExecutive | IsHR | IsCHR | IsAdmin])
def upload_feedback_csv(request):
    uploaded = request.FILES.get('file')
    if not uploaded:
        return Response({'error': 'No file provided.'}, status=status.HTTP_400_BAD_REQUEST)

    storage_path = default_storage.save(f"ingestion/csv/{uuid.uuid4()}_{uploaded.name}", uploaded)
    job = _create_job(IngestionJob.SOURCE_CSV, request, {'file_name': uploaded.name})
    parse_csv_task.delay(storage_path, request.user.id, job.id)

    return Response(
        {
            'status': 'queued',
            'job': IngestionJobSerializer(job).data,
            'message': 'CSV/Excel ingestion queued.',
        },
        status=status.HTTP_202_ACCEPTED,
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsExecutive | IsHR | IsCHR | IsAdmin])
def ingest_slack(request):
    serializer = SlackIngestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    payload = serializer.validated_data
    messages = payload.get('messages', [])
    channel = payload.get('channel', 'hr-feedback')

    if not messages:
        messages = [
            {
                'employee_email': 'alex@company.com',
                'employee_name': 'Alex Parker',
                'department': 'Engineering',
                'text': 'The release was intense, but team support was strong this week.',
                'timestamp': timezone.now().isoformat(),
            }
        ]

    for idx, message in enumerate(messages):
        email = (message.get('employee_email') or message.get('email') or '').strip()
        if not email:
            return Response(
                {'error': f'Missing employee email in Slack message at index {idx}.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

    job = _create_job(IngestionJob.SOURCE_SLACK, request, {'channel': channel, 'message_count': len(messages)})
    ingest_slack_messages_task.delay(messages, channel, request.user.id, job.id)

    return Response(
        {
            'status': 'queued',
            'job': IngestionJobSerializer(job).data,
            'message': 'Slack ingestion queued.',
        },
        status=status.HTTP_202_ACCEPTED,
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsExecutive | IsHR | IsCHR | IsAdmin])
def ingest_google_forms(request):
    serializer = FormsIngestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    payload = serializer.validated_data
    responses = payload.get('responses', [])
    form_id = payload.get('form_id', '')

    if not responses:
        responses = [
            {
                'employee_email': 'sam@company.com',
                'name': 'Sam Lee',
                'department': 'Product',
                'feedback': 'Need clearer priorities for the next sprint and less context switching.',
                'timestamp': timezone.now().isoformat(),
            }
        ]

    for idx, response in enumerate(responses):
        email = (response.get('employee_email') or response.get('email') or '').strip()
        if not email:
            return Response(
                {'error': f'Missing employee email in form response at index {idx}.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

    job = _create_job(IngestionJob.SOURCE_FORMS, request, {'form_id': form_id, 'response_count': len(responses)})
    ingest_google_forms_task.delay(responses, form_id, request.user.id, job.id)

    return Response(
        {
            'status': 'queued',
            'job': IngestionJobSerializer(job).data,
            'message': 'Google Forms ingestion queued.',
        },
        status=status.HTTP_202_ACCEPTED,
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsExecutive | IsHR | IsCHR | IsAdmin])
def upload_document(request):
    uploaded = request.FILES.get('file')
    if not uploaded:
        return Response({'error': 'No file provided.'}, status=status.HTTP_400_BAD_REQUEST)

    extension = uploaded.name.rsplit('.', 1)[-1].lower() if '.' in uploaded.name else ''
    if extension not in {'pdf', 'txt', 'docx'}:
        return Response({'error': 'Invalid document format. Allowed: pdf, txt, docx.'}, status=status.HTTP_400_BAD_REQUEST)

    participants = request.data.getlist('participants') if hasattr(request.data, 'getlist') else request.data.get('participants', [])
    if isinstance(participants, str):
        participants = [p.strip() for p in participants.split(',') if p.strip()]

    employee_id = request.data.get('employee_id')
    try:
        employee_id = int(employee_id) if employee_id not in (None, '') else None
    except (TypeError, ValueError):
        employee_id = None

    storage_path = default_storage.save(f"ingestion/docs/{uuid.uuid4()}_{uploaded.name}", uploaded)
    job = _create_job(IngestionJob.SOURCE_DOC, request, {'file_name': uploaded.name, 'participants': participants})
    ingest_document_task.delay(storage_path, uploaded.name, participants, employee_id, request.user.id, job.id)

    return Response(
        {
            'status': 'queued',
            'job': IngestionJobSerializer(job).data,
            'message': 'Document ingestion queued.',
        },
        status=status.HTTP_202_ACCEPTED,
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsExecutive | IsHR | IsCHR | IsAdmin])
def feedback_list(request):
    feedbacks = Feedback.objects.select_related('employee').all()
    feedbacks = _scope_queryset_for_user(feedbacks, request.user, 'employee__organization')[:200]
    return Response(FeedbackSerializer(feedbacks, many=True).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsExecutive | IsHR | IsCHR | IsAdmin])
def ingestion_overview(request):
    jobs_qs = _scope_queryset_for_user(IngestionJob.objects.select_related('created_by').all(), request.user, 'created_by__profile__organization')
    jobs = jobs_qs[:15]
    employee_qs = _scope_queryset_for_user(Employee.objects.all(), request.user)
    feedback_qs = _scope_queryset_for_user(Feedback.objects.all(), request.user, 'employee__organization')
    meeting_qs = _scope_queryset_for_user(Meeting.objects.all(), request.user)
    insight_qs = _scope_queryset_for_user(SentimentInsight.objects.all(), request.user, 'employee__organization')

    avg_sentiment = insight_qs.aggregate(avg=Avg('sentiment_score')).get('avg')

    data = {
        'counts': {
            'employees': employee_qs.count(),
            'feedback': feedback_qs.count(),
            'meetings': meeting_qs.count(),
            'sentiment_insights': insight_qs.count(),
            'insights': insight_qs.count(),
        },
        'avg_sentiment': round(avg_sentiment, 3) if avg_sentiment is not None else None,
        'jobs': IngestionJobSerializer(jobs, many=True).data,
        'architecture': {
            'stage_1_connectors': [
                'CSV / Excel Connector',
                'Slack Connector',
                'Google Forms Connector',
                'Document Connector',
            ],
            'stage_2_normalization': [
                'Employee Data => employee_id, name, department, manager, join_date',
                'Feedback Data => employee, source, sentiment, timestamp',
                'Meeting Data => participants, summary, sentiment',
            ],
            'stage_3_storage': ['Employee', 'Feedback', 'Meeting', 'Sentiment Insights'],
            'stage_4_ai_processing': ['sentiment analysis', 'summarization', 'insight generation'],
            'stage_5_dashboard': ['automatic profile updates via normalized records'],
        },
    }
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsExecutive | IsHR | IsCHR | IsAdmin])
def ingestion_stats(request):
    employee_qs = _scope_queryset_for_user(Employee.objects.all(), request.user)
    feedback_qs = _scope_queryset_for_user(Feedback.objects.all(), request.user, 'employee__organization')
    meeting_qs = _scope_queryset_for_user(Meeting.objects.all(), request.user)
    insight_qs = _scope_queryset_for_user(SentimentInsight.objects.all(), request.user, 'employee__organization')

    payload = {
        'employees': employee_qs.count(),
        'feedback': feedback_qs.count(),
        'meetings': meeting_qs.count(),
        'insights': insight_qs.count(),
        'sentiment_insights': insight_qs.count(),
    }
    return Response(payload)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsExecutive | IsHR | IsCHR | IsAdmin])
def ingestion_jobs(request):
    jobs = _scope_queryset_for_user(IngestionJob.objects.select_related('created_by').all(), request.user, 'created_by__profile__organization')[:50]
    return Response(IngestionJobSerializer(jobs, many=True).data)


# API aliases for connector contracts
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsExecutive | IsHR | IsCHR | IsAdmin])
def upload_feedback_csv_alias(request):
    return upload_feedback_csv(request)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsExecutive | IsHR | IsCHR | IsAdmin])
def ingest_google_forms_alias(request):
    return ingest_google_forms(request)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsExecutive | IsHR | IsCHR | IsAdmin])
def upload_document_alias(request):
    return upload_document(request)
