from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Avg, Count
from employees.models import Employee
from meetings.models import EmployeeMeetingInsight, Meeting
from .models import EmployeeInsight, MeetingEmbedding
from .serializers import EmployeeInsightSerializer, MeetingEmbeddingSerializer
from rest_framework.views import APIView


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard(request):
    """Dashboard summary endpoint."""
    user = request.user

    user_org = request.user.profile.organization if hasattr(request.user, 'profile') else None

    # ADMIN sees all data
    if hasattr(user, 'profile') and user.profile.role == 'ADMIN':
        employee_count = Employee.objects.count()
        meeting_count = Meeting.objects.count()
        dept_sentiment = (
            Meeting.objects
            .values('employee__department')
            .annotate(avg_sentiment=Avg('sentiment_score'), count=Count('id'))
            .order_by('employee__department')
        )
    elif hasattr(user, 'profile') and user.profile.organization:
        user_org = user.profile.organization
        employee_count = Employee.objects.filter(organization=user_org).count()
        meeting_count = Meeting.objects.filter(employee__organization=user_org).count()
        dept_sentiment = (
            Meeting.objects
            .filter(employee__organization=user_org)
            .values('employee__department')
            .annotate(avg_sentiment=Avg('sentiment_score'), count=Count('id'))
            .order_by('employee__department')
        )
    else:
        # Authenticated user with no org: show all data
        employee_count = Employee.objects.count()
        meeting_count = Meeting.objects.count()
        dept_sentiment = (
            Meeting.objects
            .values('employee__department')
            .annotate(avg_sentiment=Avg('sentiment_score'), count=Count('id'))
            .order_by('employee__department')
        )

    department_sentiment = [
        {
            'department': d['employee__department'],
            'avg_sentiment': round(d['avg_sentiment'], 2) if d['avg_sentiment'] else None,
            'meeting_count': d['count'],
        }
        for d in dept_sentiment
    ]

    # High attrition risk employees
    high_risk = EmployeeInsight.objects.filter(burnout_risk__gte=0.6).select_related('employee')
    high_attrition_employees = [
        {
            'id': insight.employee.id,
            'name': insight.employee.name,
            'department': insight.employee.department,
            'burnout_risk': round(insight.burnout_risk, 2),
        }
        for insight in high_risk
    ]

    # Recent meetings
    recent_meetings = Meeting.objects.select_related('employee').order_by('-date')[:5]
    recent = [
        {
            'id': m.id,
            'employee_name': m.employee.name,
            'date': m.date.isoformat(),
            'sentiment_score': m.sentiment_score,
        }
        for m in recent_meetings
    ]

    scoped_meetings = (
        Meeting.objects.all()
        if hasattr(request.user, 'profile') and request.user.profile.role == 'ADMIN'
        else Meeting.objects.filter(organization=user_org)
    )
    scoped_employee_insights = EmployeeMeetingInsight.objects.filter(meeting__in=scoped_meetings)

    team_sentiment_trend = [
        {
            'meeting_id': meeting.id,
            'date': (meeting.meeting_date or meeting.date).isoformat(),
            'sentiment_score': round(float(meeting.sentiment_score or 0.0), 4),
        }
        for meeting in scoped_meetings.order_by('-meeting_date', '-id')[:10]
    ]

    top_contributors = [
        {
            'employee_id': row['employee'],
            'employee_name': row['employee__name'],
            'avg_engagement': round(float(row['avg_engagement'] or 0.0), 4),
            'avg_turns': round(float(row['avg_turns'] or 0.0), 2),
        }
        for row in (
            scoped_employee_insights
            .values('employee', 'employee__name')
            .annotate(avg_engagement=Avg('engagement_score'), avg_turns=Avg('speaking_turns'))
            .order_by('-avg_engagement', '-avg_turns')[:5]
        )
    ]

    low_participation = [
        {
            'employee_id': row['employee'],
            'employee_name': row['employee__name'],
            'avg_engagement': round(float(row['avg_engagement'] or 0.0), 4),
            'avg_turns': round(float(row['avg_turns'] or 0.0), 2),
        }
        for row in (
            scoped_employee_insights
            .values('employee', 'employee__name')
            .annotate(avg_engagement=Avg('engagement_score'), avg_turns=Avg('speaking_turns'))
            .order_by('avg_engagement', 'avg_turns')[:5]
        )
    ]

    top_sentiment_people = [
        {
            'employee_id': row['employee'],
            'employee_name': row['employee__name'],
            'avg_sentiment': round(float(row['avg_sentiment'] or 0.0), 4),
            'meeting_count': int(row['meeting_count'] or 0),
        }
        for row in (
            scoped_employee_insights
            .values('employee', 'employee__name')
            .annotate(avg_sentiment=Avg('sentiment_score'), meeting_count=Count('meeting'))
            .order_by('-avg_sentiment', '-meeting_count')[:5]
        )
    ]

    return Response({
        'employee_count': employee_count,
        'meeting_count': meeting_count,
        'department_sentiment': department_sentiment,
        'high_attrition_employees': high_attrition_employees,
        'recent_meetings': recent,
        'meeting_intelligence': {
            'team_sentiment_trend': team_sentiment_trend,
            'employee_engagement_chart': top_contributors,
            'top_contributors': top_contributors,
            'low_participation_employees': low_participation,
            'top_sentiment_people': top_sentiment_people,
        },
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def employee_insights(request, employee_id):
    """Get AI-extracted insights for an employee."""
    try:
        insight = EmployeeInsight.objects.select_related('employee').get(employee_id=employee_id)
    except EmployeeInsight.DoesNotExist:
        return Response({'error': 'No insights found for this employee'}, status=status.HTTP_404_NOT_FOUND)
    return Response(EmployeeInsightSerializer(insight).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def attrition_risk(request, employee_id):
    """Get attrition risk score for an employee."""
    try:
        employee = Employee.objects.get(id=employee_id)
    except Employee.DoesNotExist:
        return Response({'error': 'Employee not found'}, status=status.HTTP_404_NOT_FOUND)

    from ai_engine.attrition import calculate_attrition_risk
    risk_data = calculate_attrition_risk(employee_id)

    return Response({
        'employee_id': employee_id,
        'employee_name': employee.name,
        **risk_data,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def attrition_risk_lookup(request):
    """GET /api/analytics/attrition/?employee_id=123"""
    employee_id = request.query_params.get('employee_id')
    if not employee_id:
        return Response({'error': 'employee_id query parameter is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        employee_id_int = int(employee_id)
    except (TypeError, ValueError):
        return Response({'error': 'employee_id must be an integer'}, status=status.HTTP_400_BAD_REQUEST)

    return attrition_risk(request, employee_id_int)


class MeetingEmbeddingAPI(APIView):
    def get(self, request, meeting_id):
        """Get embedding for a meeting."""
        try:
            embedding = MeetingEmbedding.objects.get(meeting_id=meeting_id)
        except MeetingEmbedding.DoesNotExist:
            return Response({'error': 'No embedding found for this meeting'}, status=status.HTTP_404_NOT_FOUND)
        return Response(MeetingEmbeddingSerializer(embedding).data)
