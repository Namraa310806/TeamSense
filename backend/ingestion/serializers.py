
from rest_framework import serializers
from .models import Feedback, Document, IngestionJob
from employees.serializers import EmployeeSerializer


class FeedbackSerializer(serializers.ModelSerializer):
    employee = EmployeeSerializer(read_only=True)

    class Meta:
        model = Feedback
        fields = '__all__'


class FeedbackUploadSerializer(serializers.Serializer):
    employee_id = serializers.IntegerField(required=False)
    source = serializers.ChoiceField(choices=Feedback.SOURCE_CHOICES)
    content = serializers.CharField()
    timestamp = serializers.DateTimeField()
    raw_data = serializers.JSONField(default=dict, required=False)


class DocumentUploadSerializer(serializers.Serializer):
    employee_id = serializers.IntegerField(required=False)
    file = serializers.FileField()
    participants = serializers.ListField(
        child=serializers.CharField(), required=False, allow_empty=True
    )


class IngestionJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = IngestionJob
        fields = '__all__'


class SlackIngestSerializer(serializers.Serializer):
    channel = serializers.CharField(required=False, allow_blank=True, default='hr-feedback')
    messages = serializers.ListField(child=serializers.JSONField(), required=False, allow_empty=True)


class FormsIngestSerializer(serializers.Serializer):
    form_id = serializers.CharField(required=False, allow_blank=True)
    responses = serializers.ListField(child=serializers.JSONField(), required=False, allow_empty=True)

