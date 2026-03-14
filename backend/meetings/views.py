from django.db.models import Avg, Q
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.models import Organization
from accounts.permissions import IsAdmin, IsExecutive, IsHR
from analytics.models import MeetingAnalysis
from analytics.serializers import MeetingAnalysisSerializer
from employees.models import Employee
from meetings.models import EmployeeMeetingInsight, Meeting, MeetingInsight, MeetingParticipant, MeetingSpeakerMapping, MeetingTranscript
from meetings.services.meeting_service import schedule_text_meeting_pipeline, schedule_uploaded_meeting_pipeline
from meetings.serializers import (
    EmployeeMeetingInsightSerializer,
    MapSpeakersSerializer,
    MeetingInsightSerializer,
    MeetingSerializer,
    MeetingSpeakerMappingSerializer,
    MeetingTranscriptSerializer,
    MeetingUploadSerializer,
    RecordingUploadSerializer,
)


def _user_org(user):
    return user.profile.organization if hasattr(user, 'profile') else None


def _is_admin(user):
    return hasattr(user, 'profile') and user.profile.role == 'ADMIN'


def _resolve_org_for_meeting(request, organization_id=None):
    user_org = _user_org(request.user)
    if organization_id is None:
        return user_org

    try:
        org = Organization.objects.get(id=organization_id)
    except Organization.DoesNotExist:
        raise ValueError('Invalid organization_id')

    if _is_admin(request.user):
        return org

    if user_org and user_org.id == org.id:
        return org

    raise PermissionError('Permission denied for this organization')


def _resolve_employees(participants, organization):
    employee_ids = []
    for value in participants or []:
        try:
            employee_ids.append(int(value))
        except (TypeError, ValueError):
            continue

    if not employee_ids:
        raise ValueError('participants must include valid employee IDs')

    employees = list(Employee.objects.filter(id__in=employee_ids))
    if len(employees) != len(set(employee_ids)):
        raise ValueError('One or more participants were not found')

    if organization is not None:
        for employee in employees:
            if employee.organization_id != organization.id:
                raise PermissionError('Participant belongs to a different organization')

    order = {emp_id: idx for idx, emp_id in enumerate(employee_ids)}
    employees.sort(key=lambda item: order.get(item.id, 0))
    return employees


def _attach_participants(meeting, employees):
    existing = set(MeetingParticipant.objects.filter(meeting=meeting).values_list('employee_id', flat=True))
    rows = [MeetingParticipant(meeting=meeting, employee=emp) for emp in employees if emp.id not in existing]
    if rows:
        MeetingParticipant.objects.bulk_create(rows)


def _meeting_queryset_for_user(request):
    org = _user_org(request.user)
    if _is_admin(request.user):
        return Meeting.objects.select_related('employee', 'organization', 'uploaded_by')
    if org:
        return Meeting.objects.select_related('employee', 'organization', 'uploaded_by').filter(organization=org)
    # Demo mode: if no organization is assigned, do not hide all meetings.
    return Meeting.objects.select_related('employee', 'organization', 'uploaded_by')


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsExecutive | IsHR | IsAdmin])
def upload_meeting(request):
    """POST /api/meetings/upload/

    Upload transcript/audio/video meeting with participants and schedule analysis.
    """
    serializer = MeetingUploadSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    try:
        organization = _resolve_org_for_meeting(request, data.get('organization_id'))
        employees = _resolve_employees(data.get('participants', []), organization)
    except PermissionError as exc:
        return Response({'error': str(exc)}, status=status.HTTP_403_FORBIDDEN)
    except ValueError as exc:
        return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    owner = employees[0]
    meeting_date = data.get('meeting_date', timezone.now().date())
    transcript_text = (data.get('transcript') or '').strip()
    meeting_file = data.get('meeting_file')

    meeting = Meeting.objects.create(
        organization=organization,
        meeting_title=data.get('meeting_title', ''),
        department=data.get('department', owner.department),
        meeting_date=meeting_date,
        uploaded_by=request.user,
        meeting_file=meeting_file,
        transcript_status=Meeting.TRANSCRIPT_STATUS_PENDING,
        employee=owner,
        date=meeting_date,
        transcript=transcript_text,
    )
    _attach_participants(meeting, employees)

    # transcript_text always has priority when both transcript and recording are submitted.
    if transcript_text:
        pipeline_status = schedule_text_meeting_pipeline(meeting.id)
    elif meeting.meeting_file:
        pipeline_status = schedule_uploaded_meeting_pipeline(meeting.id)
    else:
        return Response({'error': 'Provide transcript_text or meeting_file.'}, status=status.HTTP_400_BAD_REQUEST)

    return Response(
        {
            'message': 'Meeting uploaded successfully',
            'meeting': MeetingSerializer(meeting).data,
            'participants': [{'id': emp.id, 'name': emp.name} for emp in employees],
            'pipeline_status': pipeline_status,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsExecutive | IsHR | IsAdmin])
def meeting_list(request):
    queryset = _meeting_queryset_for_user(request)

    employee_id = request.query_params.get('employee_id')
    if employee_id:
        queryset = queryset.filter(Q(employee_id=employee_id) | Q(participants__employee_id=employee_id)).distinct()

    serializer = MeetingSerializer(queryset.order_by('-meeting_date', '-id'), many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsExecutive | IsHR | IsAdmin])
def meeting_detail(request, pk):
    meeting = _meeting_queryset_for_user(request).filter(id=pk).first()
    if not meeting:
        return Response({'error': 'Meeting not found'}, status=status.HTTP_404_NOT_FOUND)

    payload = MeetingSerializer(meeting).data
    payload['transcript_segments'] = MeetingTranscriptSerializer(
        meeting.transcript_segments.all().order_by('start_time', 'id'), many=True
    ).data
    payload['speaker_mapping'] = MeetingSpeakerMappingSerializer(meeting.speaker_mappings.all(), many=True).data

    return Response(payload)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsExecutive | IsHR | IsAdmin])
def meeting_transcript(request):
    """GET /api/meetings/transcript/?meeting_id=1"""
    meeting_id = request.query_params.get('meeting_id')
    if not meeting_id:
        return Response({'error': 'meeting_id is required'}, status=status.HTTP_400_BAD_REQUEST)

    meeting = _meeting_queryset_for_user(request).filter(id=meeting_id).first()
    if not meeting:
        return Response({'error': 'Meeting not found'}, status=status.HTTP_404_NOT_FOUND)

    return Response(
        {
            'meeting_id': meeting.id,
            'transcript_status': meeting.transcript_status,
            'transcript': meeting.transcript,
            'segments': MeetingTranscriptSerializer(
                meeting.transcript_segments.all().order_by('start_time', 'id'), many=True
            ).data,
        }
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsExecutive | IsHR | IsAdmin])
def meeting_summary(request):
    """GET /api/meetings/summary/?meeting_id=1"""
    meeting_id = request.query_params.get('meeting_id')
    if not meeting_id:
        return Response({'error': 'meeting_id is required'}, status=status.HTTP_400_BAD_REQUEST)

    meeting = _meeting_queryset_for_user(request).filter(id=meeting_id).first()
    if not meeting:
        return Response({'error': 'Meeting not found'}, status=status.HTTP_404_NOT_FOUND)

    return Response(
        {
            'meeting_id': meeting.id,
            'summary': meeting.summary,
            'sentiment_score': meeting.sentiment_score,
            'transcript_status': meeting.transcript_status,
        }
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsExecutive | IsHR | IsAdmin])
def map_speakers(request):
    """POST /api/meetings/map-speakers/

    Body: {"meeting_id": 1, "speaker_mapping": {"Speaker_1": 3, "Speaker_2": 7}}
    """
    serializer = MapSpeakersSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    payload = serializer.validated_data
    meeting = _meeting_queryset_for_user(request).filter(id=payload['meeting_id']).first()
    if not meeting:
        return Response({'error': 'Meeting not found'}, status=status.HTTP_404_NOT_FOUND)

    org = meeting.organization
    update_items = []
    for speaker_label, employee_id in payload['speaker_mapping'].items():
        employee = None
        if employee_id is not None:
            try:
                employee = Employee.objects.get(id=employee_id)
            except Employee.DoesNotExist:
                return Response({'error': f'Employee not found for {speaker_label}'}, status=status.HTTP_400_BAD_REQUEST)
            if org and employee.organization_id != org.id:
                return Response({'error': f'Employee for {speaker_label} is outside organization'}, status=status.HTTP_403_FORBIDDEN)

        mapping, _ = MeetingSpeakerMapping.objects.update_or_create(
            meeting=meeting,
            speaker_label=speaker_label,
            defaults={'employee': employee},
        )
        update_items.append(mapping)

    return Response(
        {
            'message': 'Speaker mapping updated',
            'mapping': MeetingSpeakerMappingSerializer(update_items, many=True).data,
        }
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsExecutive | IsHR | IsAdmin])
def meeting_insights(request, meeting_id):
    meeting = _meeting_queryset_for_user(request).filter(id=meeting_id).first()
    if not meeting:
        return Response({'error': 'Meeting not found'}, status=status.HTTP_404_NOT_FOUND)

    try:
        analysis = MeetingAnalysis.objects.get(meeting=meeting)
    except MeetingAnalysis.DoesNotExist:
        return Response({'error': 'Insights not ready yet'}, status=status.HTTP_404_NOT_FOUND)

    employee_insights = EmployeeMeetingInsight.objects.filter(meeting=meeting).select_related('employee')
    meeting_insights_rows = MeetingInsight.objects.filter(meeting=meeting).order_by('-created_at', 'id')

    team_sentiment = analysis.employee_sentiment_scores.get('overall', {}).get('scores', {})
    dominant = employee_insights.order_by('-speaking_turns', '-participation_duration')[:3]
    low_participation = employee_insights.order_by('speaking_turns', 'participation_duration')[:3]

    return Response(
        {
            'meeting': MeetingSerializer(meeting).data,
            'analysis': MeetingAnalysisSerializer(analysis).data,
            'team_sentiment_score': float(team_sentiment.get('positive', 0.0)),
            'employee_engagement': EmployeeMeetingInsightSerializer(employee_insights, many=True).data,
            'meeting_insights': MeetingInsightSerializer(meeting_insights_rows, many=True).data,
            'top_contributors': EmployeeMeetingInsightSerializer(dominant, many=True).data,
            'low_participation_employees': EmployeeMeetingInsightSerializer(low_participation, many=True).data,
        }
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsExecutive | IsHR | IsAdmin])
def upload_meeting_recording(request):
    """Backward-compatible endpoint that forwards to upload contract.

    Accepts: employee_ids + recording + optional date.
    """
    serializer = RecordingUploadSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    payload = serializer.validated_data
    wrapped_payload = {
        'organization_id': request.data.get('organization_id'),
        'meeting_title': request.data.get('meeting_title', ''),
        'department': request.data.get('department', ''),
        'meeting_date': payload.get('date') or timezone.now().date(),
        'participants': payload.get('employee_ids') or ([payload.get('employee_id')] if payload.get('employee_id') else []),
        'meeting_file': payload.get('recording'),
    }

    proxy_serializer = MeetingUploadSerializer(data=wrapped_payload)
    if not proxy_serializer.is_valid():
        return Response({'error': proxy_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    data = proxy_serializer.validated_data
    try:
        organization = _resolve_org_for_meeting(request, data.get('organization_id'))
        employees = _resolve_employees(data.get('participants', []), organization)
    except PermissionError as exc:
        return Response({'error': str(exc)}, status=status.HTTP_403_FORBIDDEN)
    except ValueError as exc:
        return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    owner = employees[0]
    meeting = Meeting.objects.create(
        organization=organization,
        meeting_title=data.get('meeting_title', ''),
        department=data.get('department', owner.department),
        meeting_date=data.get('meeting_date') or timezone.now().date(),
        uploaded_by=request.user,
        meeting_file=data.get('meeting_file'),
        transcript_status=Meeting.TRANSCRIPT_STATUS_PENDING,
        employee=owner,
        date=data.get('meeting_date') or timezone.now().date(),
        transcript='',
    )
    _attach_participants(meeting, employees)

    pipeline_status = schedule_uploaded_meeting_pipeline(meeting.id)

    return Response(
        {
            'message': 'Meeting recording uploaded successfully',
            'meeting': MeetingSerializer(meeting).data,
            'participants': [{'id': emp.id, 'name': emp.name} for emp in employees],
            'pipeline_status': pipeline_status,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsExecutive | IsHR | IsAdmin])
def meeting_analysis_detail(request, meeting_id):
    return meeting_insights(request, meeting_id)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsExecutive | IsHR | IsAdmin])
def employee_meeting_insights(request, employee_id):
    org = _user_org(request.user)
    employee = Employee.objects.filter(id=employee_id).first()
    if not employee:
        return Response({'error': 'Employee not found'}, status=status.HTTP_404_NOT_FOUND)

    if org and employee.organization_id and employee.organization_id != org.id and not _is_admin(request.user):
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

    insights = EmployeeMeetingInsight.objects.filter(employee_id=employee_id).select_related('meeting').order_by('-meeting__meeting_date', '-id')
    if not insights.exists():
        return Response({'error': 'No meeting analyses found for this employee'}, status=status.HTTP_404_NOT_FOUND)

    avg_engagement = insights.aggregate(avg=Avg('engagement_score')).get('avg') or 0.0

    sentiment_trend = [
        {
            'meeting_id': item.meeting_id,
            'date': (item.meeting.meeting_date or item.meeting.date).isoformat(),
            'sentiment_score': round(float(item.sentiment_score), 4),
        }
        for item in insights
    ]
    participation_frequency = [
        {
            'meeting_id': item.meeting_id,
            'date': (item.meeting.meeting_date or item.meeting.date).isoformat(),
            'speaking_turns': item.speaking_turns,
            'participation_duration': round(float(item.participation_duration), 3),
        }
        for item in insights
    ]

    latest_meeting = insights.first().meeting
    latest_analysis = MeetingAnalysis.objects.filter(meeting=latest_meeting).first()

    return Response(
        {
            'employee_id': employee_id,
            'meeting_count': insights.count(),
            'engagement_score': round(float(avg_engagement), 4),
            'sentiment_trend': sentiment_trend,
            'participation_frequency': participation_frequency,
            'latest_analysis': MeetingAnalysisSerializer(latest_analysis).data if latest_analysis else None,
        }
    )
