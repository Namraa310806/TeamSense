from django.db import models
from employees.models import Employee
from meetings.models import Meeting


class EmployeeInsight(models.Model):
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='insight')
    topics = models.JSONField(default=list, blank=True)
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
