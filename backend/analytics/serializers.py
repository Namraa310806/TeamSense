from rest_framework import serializers
from .models import EmployeeInsight, MeetingEmbedding, MeetingAnalysis


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


class MeetingAnalysisSerializer(serializers.ModelSerializer):
    employee_id = serializers.IntegerField(source='meeting.employee_id', read_only=True)
    employee_name = serializers.CharField(source='meeting.employee.name', read_only=True)
    meeting_date = serializers.DateField(source='meeting.date', read_only=True)

    class Meta:
        model = MeetingAnalysis
        fields = [
            'id',
            'meeting',
            'meeting_date',
            'employee_id',
            'employee_name',
            'transcript',
            'summary',
            'employee_sentiment_scores',
            'participation_score',
            'collaboration_signals',
            'engagement_signals',
            'conflict_detection',
            'speaker_mapping',
            'created_at',
            'updated_at',
        ]
