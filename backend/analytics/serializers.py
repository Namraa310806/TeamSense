from rest_framework import serializers
from .models import EmployeeInsight, MeetingEmbedding


class EmployeeInsightSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.name', read_only=True)

    class Meta:
        model = EmployeeInsight
        fields = '__all__'


class MeetingEmbeddingSerializer(serializers.ModelSerializer):
    embedding = serializers.ListField(child=serializers.FloatField(), read_only=True)

    class Meta:
        model = MeetingEmbedding
        fields = ['id', 'meeting', 'created_at']
