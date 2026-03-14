import uuid

from django.core.files.storage import default_storage
from django.db.models import Avg
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

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


def _create_job(source, request, metadata=None):
    return IngestionJob.objects.create(
        source=source,
        status=IngestionJob.STATUS_QUEUED,
        created_by=request.user,
        metadata=metadata or {},
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
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
@permission_classes([IsAuthenticated])
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
@permission_classes([IsAuthenticated])
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
@permission_classes([IsAuthenticated])
def upload_document(request):
    uploaded = request.FILES.get('file')
    if not uploaded:
        return Response({'error': 'No file provided.'}, status=status.HTTP_400_BAD_REQUEST)

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
@permission_classes([IsAuthenticated])
def feedback_list(request):
    feedbacks = Feedback.objects.select_related('employee').all()[:200]
    return Response(FeedbackSerializer(feedbacks, many=True).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ingestion_overview(request):
    jobs = IngestionJob.objects.all()[:15]
    avg_sentiment = SentimentInsight.objects.aggregate(avg=Avg('sentiment_score')).get('avg')

    data = {
        'counts': {
            'employees': Employee.objects.count(),
            'feedback': Feedback.objects.count(),
            'meetings': Meeting.objects.count(),
            'sentiment_insights': SentimentInsight.objects.count(),
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
@permission_classes([IsAuthenticated])
def ingestion_jobs(request):
    jobs = IngestionJob.objects.all()[:50]
    return Response(IngestionJobSerializer(jobs, many=True).data)
