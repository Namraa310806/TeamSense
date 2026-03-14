from django.db import models
from django.contrib.auth.models import User
from accounts.models import Organization
from employees.models import Employee


class Meeting(models.Model):
    TRANSCRIPT_STATUS_PENDING = 'PENDING'
    TRANSCRIPT_STATUS_PROCESSING = 'PROCESSING'
    TRANSCRIPT_STATUS_COMPLETED = 'COMPLETED'
    TRANSCRIPT_STATUS_FAILED = 'FAILED'
    TRANSCRIPT_STATUS_CHOICES = [
        (TRANSCRIPT_STATUS_PENDING, 'Pending'),
        (TRANSCRIPT_STATUS_PROCESSING, 'Processing'),
        (TRANSCRIPT_STATUS_COMPLETED, 'Completed'),
        (TRANSCRIPT_STATUS_FAILED, 'Failed'),
    ]

    organization = models.ForeignKey(
        Organization,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='meetings',
    )
    meeting_title = models.CharField(max_length=255, blank=True, default='')
    department = models.CharField(max_length=255, blank=True, default='')
    meeting_date = models.DateField(null=True, blank=True)
    uploaded_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='uploaded_meetings',
    )
    meeting_file = models.FileField(upload_to='meetings/%Y/%m/%d/', null=True, blank=True)
    transcript_status = models.CharField(
        max_length=20,
        choices=TRANSCRIPT_STATUS_CHOICES,
        default=TRANSCRIPT_STATUS_PENDING,
    )

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='meetings')
    date = models.DateField()
    transcript = models.TextField(blank=True, default='')
    summary = models.TextField(blank=True, default='')
    sentiment_score = models.FloatField(null=True, blank=True)
    key_topics = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"Meeting with {self.employee.name} on {self.date}"


class MeetingParticipant(models.Model):
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name='participants')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='meeting_participations')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('meeting', 'employee')

    def __str__(self):
        return f"{self.employee.name} in Meeting {self.meeting_id}"


class MeetingTranscript(models.Model):
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name='transcript_segments')
    speaker = models.CharField(max_length=100)
    speaker_employee = models.ForeignKey(
        Employee,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='spoken_transcript_segments',
    )
    text = models.TextField()
    start_time = models.FloatField(default=0.0)
    end_time = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['meeting_id', 'start_time', 'id']

    def __str__(self):
        return f"{self.speaker} ({self.start_time:.2f}-{self.end_time:.2f})"


class MeetingInsight(models.Model):
    TYPE_SUMMARY = 'SUMMARY'
    TYPE_ACTION_ITEM = 'ACTION_ITEM'
    TYPE_TOPIC = 'TOPIC'
    TYPE_RISK = 'RISK'
    TYPE_CHOICES = [
        (TYPE_SUMMARY, 'Summary'),
        (TYPE_ACTION_ITEM, 'Action Item'),
        (TYPE_TOPIC, 'Topic'),
        (TYPE_RISK, 'Risk'),
    ]

    SEVERITY_LOW = 'LOW'
    SEVERITY_MEDIUM = 'MEDIUM'
    SEVERITY_HIGH = 'HIGH'
    SEVERITY_CHOICES = [
        (SEVERITY_LOW, 'Low'),
        (SEVERITY_MEDIUM, 'Medium'),
        (SEVERITY_HIGH, 'High'),
    ]

    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name='insights')
    insight_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    description = models.TextField()
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default=SEVERITY_LOW)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', 'id']

    def __str__(self):
        return f"{self.insight_type} insight for meeting {self.meeting_id}"


class MeetingSpeakerMapping(models.Model):
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name='speaker_mappings')
    speaker_label = models.CharField(max_length=100)
    employee = models.ForeignKey(
        Employee,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='speaker_mappings',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('meeting', 'speaker_label')
        ordering = ['meeting_id', 'speaker_label']

    def __str__(self):
        return f"{self.speaker_label} -> {self.employee.name if self.employee else 'Unmapped'}"


class EmployeeMeetingInsight(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='meeting_insights')
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name='employee_insights')
    participation_duration = models.FloatField(default=0.0)
    sentiment_score = models.FloatField(default=0.0)
    engagement_score = models.FloatField(default=0.0)
    speaking_turns = models.PositiveIntegerField(default=0)
    interruption_signals = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('employee', 'meeting')
        ordering = ['-meeting__date', '-id']

    def __str__(self):
        return f"{self.employee.name} insight for meeting {self.meeting_id}"
