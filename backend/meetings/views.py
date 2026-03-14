from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from .models import Meeting
from .serializers import MeetingSerializer, MeetingUploadSerializer
from employees.models import Employee


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_meeting(request):
    """Upload a meeting transcript and trigger AI pipeline."""
    user_org = request.user.profile.organization if hasattr(request.user, 'profile') else None
    employee_id = request.data.get('employee_id')
    if employee_id:
        try:
            employee = Employee.objects.get(id=employee_id)
            if user_org and employee.organization and employee.organization != user_org:
                return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        except Employee.DoesNotExist:
            return Response({'error': 'Employee not found'}, status=status.HTTP_404_NOT_FOUND)

    serializer = MeetingUploadSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    try:
        employee = Employee.objects.get(id=data['employee_id'])
    except Employee.DoesNotExist:
        return Response({'error': 'Employee not found'}, status=status.HTTP_404_NOT_FOUND)

    meeting = Meeting.objects.create(
        employee=employee,
        transcript=data['transcript'],
        date=data.get('date', timezone.now().date()),
    )

    # Trigger async AI pipeline
    try:
        from .tasks import process_transcript_task
        process_transcript_task.delay(meeting.id)
        pipeline_status = 'processing'
    except Exception:
        # Run synchronously if Celery is not available
        from ai_engine.pipeline import run_pipeline
        run_pipeline(meeting.id)
        pipeline_status = 'completed'

    return Response({
        'id': meeting.id,
        'message': 'Meeting uploaded successfully',
        'pipeline_status': pipeline_status,
        'meeting': MeetingSerializer(meeting).data,
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def meeting_list(request):
    """List all meetings, optionally filtered by employee_id."""
    user_org = request.user.profile.organization if hasattr(request.user, 'profile') else None
    employee_id = request.query_params.get('employee_id')
    if employee_id:
        try:
            employee = Employee.objects.get(id=employee_id)
            if user_org and employee.organization and employee.organization != user_org:
                return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        except Employee.DoesNotExist:
            return Response({'error': 'Employee not found'}, status=status.HTTP_404_NOT_FOUND)

    meetings = Meeting.objects.all()
    if employee_id:
        meetings = meetings.filter(employee_id=employee_id)
    serializer = MeetingSerializer(meetings, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def meeting_detail(request, pk):
    """Get meeting detail with full transcript, summary, and topics."""
    try:
        meeting = Meeting.objects.get(pk=pk)
    except Meeting.DoesNotExist:
        return Response({'error': 'Meeting not found'}, status=status.HTTP_404_NOT_FOUND)

    return Response(MeetingSerializer(meeting).data)
