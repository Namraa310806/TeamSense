from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Employee
from .serializers import EmployeeSerializer, EmployeeListSerializer
from meetings.models import Meeting
from meetings.serializers import MeetingSerializer
from analytics.models import EmployeeInsight
from analytics.serializers import EmployeeInsightSerializer
from accounts.permissions import IsAdmin, IsExecutive, IsHR, IsSameOrganization


class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.prefetch_related('meetings').all()

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAdmin() or IsExecutive() or IsHR()]
        elif self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsExecutive() or IsHR()]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'profile') and user.profile.role == 'ADMIN':
            return Employee.objects.all()
        elif hasattr(user, 'profile') and user.profile.organization:
            return Employee.objects.filter(organization=user.profile.organization)
        return Employee.objects.none()

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
