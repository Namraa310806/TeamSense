
from rest_framework import serializers
from .models import Feedback, Document
from employees.serializers import EmployeeSerializer


class FeedbackSerializer(serializers.ModelSerializer):
    employee = EmployeeSerializer(read_only=True)

    class Meta:
        model = Feedback
        fields = '__all__'


class FeedbackUploadSerializer(serializers.Serializer):
    employee_id = serializers.IntegerField()
    source = serializers.ChoiceField(choices=Feedback.SOURCES)
    content = serializers.CharField()
    timestamp = serializers.DateTimeField()
    raw_data = serializers.JSONField(default=dict, required=False)


class DocumentUploadSerializer(serializers.Serializer):
    employee_id = serializers.IntegerField(required=False)
    file = serializers.FileField()

