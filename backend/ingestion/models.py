
from django.db import models
from django.utils import timezone
from employees.models import Employee


class Feedback(models.Model):
    SOURCES = [
        ('csv', 'CSV/Excel'),
        ('slack', 'Slack'),
        ('forms', 'Google Forms'),
        ('doc', 'Document'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='feedbacks')
    source = models.CharField(max_length=10, choices=SOURCES)
    content = models.TextField()
    sentiment = models.FloatField(null=True, blank=True)
    timestamp = models.DateTimeField()
    raw_data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"Feedback from {self.source} for {self.employee.name}"


class Document(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, null=True, blank=True, related_name='documents')
    file_name = models.CharField(max_length=255)
    content = models.TextField()
    summary = models.TextField(blank=True)
    sentiment = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Document {self.file_name}"

