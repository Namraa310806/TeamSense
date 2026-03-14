
from django.conf import settings
from django.db import models
from employees.models import Employee


class Feedback(models.Model):
    SOURCE_CSV = 'csv'
    SOURCE_SLACK = 'slack'
    SOURCE_FORMS = 'forms'
    SOURCE_DOC = 'doc'
    SOURCE_CHOICES = [
        (SOURCE_CSV, 'CSV/Excel'),
        (SOURCE_SLACK, 'Slack'),
        (SOURCE_FORMS, 'Google Forms'),
        (SOURCE_DOC, 'Document'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='feedbacks')
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES)
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
    raw_data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Document {self.file_name}"


class IngestionJob(models.Model):
    STATUS_QUEUED = 'queued'
    STATUS_PROCESSING = 'processing'
    STATUS_COMPLETED = 'completed'
    STATUS_FAILED = 'failed'
    STATUS_CHOICES = [
        (STATUS_QUEUED, 'Queued'),
        (STATUS_PROCESSING, 'Processing'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_FAILED, 'Failed'),
    ]

    SOURCE_CSV = 'csv'
    SOURCE_SLACK = 'slack'
    SOURCE_FORMS = 'forms'
    SOURCE_DOC = 'doc'
    SOURCE_CHOICES = [
        (SOURCE_CSV, 'CSV/Excel'),
        (SOURCE_SLACK, 'Slack'),
        (SOURCE_FORMS, 'Google Forms'),
        (SOURCE_DOC, 'Document'),
    ]

    source = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_QUEUED)
    records_processed = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True, default='')
    metadata = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='ingestion_jobs',
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.source} ingestion ({self.status})"

