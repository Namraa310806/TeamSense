from rest_framework import serializers
from .models import Employee


class EmployeeSerializer(serializers.ModelSerializer):
    meeting_count = serializers.SerializerMethodField()
    avg_sentiment = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = '__all__'

    def get_meeting_count(self, obj):
        return obj.meetings.count() if hasattr(obj, 'meetings') else 0

    def get_avg_sentiment(self, obj):
        meetings = obj.meetings.all() if hasattr(obj, 'meetings') else []
        scores = [m.sentiment_score for m in meetings if m.sentiment_score is not None]
        return round(sum(scores) / len(scores), 2) if scores else None


class EmployeeListSerializer(serializers.ModelSerializer):
    meeting_count = serializers.SerializerMethodField()
    avg_sentiment = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = ['id', 'name', 'role', 'department', 'join_date', 'manager', 'email', 'meeting_count', 'avg_sentiment']

    def get_meeting_count(self, obj):
        return obj.meetings.count() if hasattr(obj, 'meetings') else 0

    def get_avg_sentiment(self, obj):
        meetings = obj.meetings.all() if hasattr(obj, 'meetings') else []
        scores = [m.sentiment_score for m in meetings if m.sentiment_score is not None]
        return round(sum(scores) / len(scores), 2) if scores else None
