from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from .models import Employee
from .serializers import EmployeeSerializer, EmployeeListSerializer
from meetings.models import EmployeeMeetingInsight, Meeting
from meetings.serializers import EmployeeMeetingInsightSerializer, MeetingSerializer
from analytics.models import EmployeeInsight
from analytics.serializers import EmployeeInsightSerializer, MeetingAnalysisSerializer
from analytics.models import MeetingAnalysis


class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.prefetch_related('meetings').all()
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Employee.objects.none()
        # ADMIN sees all employees
        if hasattr(user, 'profile') and user.profile.role == 'ADMIN':
            return Employee.objects.all()
        # Users with an org see their org's employees
        if hasattr(user, 'profile') and user.profile.organization:
            return Employee.objects.filter(organization=user.profile.organization)
        # HR/CHR/EXECUTIVE with no org assigned see all employees
        return Employee.objects.all()

    def get_serializer_class(self):
        if self.action == 'list':
            return EmployeeListSerializer
        return EmployeeSerializer

    def retrieve(self, request, *args, **kwargs):
        employee = self.get_object()
        serializer = EmployeeSerializer(employee)
        data = serializer.data

        # Include meetings
        meetings = Meeting.objects.filter(employee=employee).order_by('-date')
        data['meetings'] = MeetingSerializer(meetings, many=True).data

        # Include insights
        try:
            insight = EmployeeInsight.objects.get(employee=employee)
            data['insights'] = EmployeeInsightSerializer(insight).data
        except EmployeeInsight.DoesNotExist:
            data['insights'] = None

        return Response(data)

    @action(detail=True, methods=['get'], url_path='meeting-insights')
    def meeting_insights(self, request, pk=None):
        employee = self.get_object()
        insights = (
            EmployeeMeetingInsight.objects
            .filter(employee=employee)
            .select_related('meeting')
            .order_by('-meeting__meeting_date', '-id')
        )

        if not insights.exists():
            return Response({'error': 'No meeting analyses found for this employee'}, status=status.HTTP_404_NOT_FOUND)

        latest_meeting = insights.first().meeting
        latest_analysis = MeetingAnalysis.objects.filter(meeting=latest_meeting).first()

        sentiment_trend = [
            {
                'meeting_id': item.meeting_id,
                'date': (item.meeting.meeting_date or item.meeting.date).isoformat(),
                'positive_score': round(float(item.sentiment_score), 4),
            }
            for item in insights
        ]

        participation_frequency = [
            {
                'meeting_id': item.meeting_id,
                'date': (item.meeting.meeting_date or item.meeting.date).isoformat(),
                'participation_score': round(float(item.engagement_score), 4),
            }
            for item in insights
        ]

        return Response(
            {
                'employee_id': employee.id,
                'meeting_count': insights.count(),
                'engagement_score': round(
                    sum(float(item.engagement_score) for item in insights) / max(insights.count(), 1),
                    4,
                ),
                'sentiment_trend': sentiment_trend,
                'participation_frequency': participation_frequency,
                'insights': EmployeeMeetingInsightSerializer(insights, many=True).data,
                'latest_analysis': MeetingAnalysisSerializer(latest_analysis).data if latest_analysis else None,
            }
        )
