from django.db import models
from django.utils import timezone
from employees.models import Employee
from meetings.models import Meeting


class EmployeeInsight(models.Model):
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='insight')
    topics = models.JSONField(default=list, blank=True)
    profile_metrics = models.JSONField(default=dict, blank=True)
    career_goals = models.TextField(blank=True, default='')
    concerns = models.TextField(blank=True, default='')
    burnout_risk = models.FloatField(default=0.0)
    strengths = models.TextField(blank=True, default='')
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Insights for {self.employee.name}"


class MeetingEmbedding(models.Model):
    meeting = models.OneToOneField(Meeting, on_delete=models.CASCADE, related_name='embedding_record')
    embedding = models.JSONField(default=list)  # Store as JSON; use pgvector in production
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Embedding for Meeting {self.meeting.id}"


class MeetingAnalysis(models.Model):
    meeting = models.OneToOneField(Meeting, on_delete=models.CASCADE, related_name='analysis')
    transcript = models.TextField()
    summary = models.TextField(blank=True, default='')
    employee_sentiment_scores = models.JSONField(default=dict, blank=True)
    participation_score = models.FloatField(default=0.0)
    collaboration_signals = models.JSONField(default=dict, blank=True)
    engagement_signals = models.JSONField(default=dict, blank=True)
    conflict_detection = models.JSONField(default=dict, blank=True)
    speaker_mapping = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Analysis for Meeting {self.meeting.id}"


class SentimentInsight(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='sentiment_insights')
    source_type = models.CharField(max_length=20, default='feedback')  # feedback, meeting, doc
    sentiment_score = models.FloatField()
    insights = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Sentiment {self.sentiment_score:.2f} for {self.employee.name}"

