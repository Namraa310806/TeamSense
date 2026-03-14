from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Avg, Count
from employees.models import Employee
from meetings.models import Meeting
from .models import EmployeeInsight
from .serializers import EmployeeInsightSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard(request):
    """Dashboard summary endpoint."""
    user = request.user

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

    return Response({
        'employee_count': employee_count,
        'meeting_count': meeting_count,
        'department_sentiment': department_sentiment,
        'high_attrition_employees': high_attrition_employees,
        'recent_meetings': recent,
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
