from django.db import models
from employees.models import Employee


class Meeting(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='meetings')
    date = models.DateField()
    transcript = models.TextField()
    summary = models.TextField(blank=True, default='')
    sentiment_score = models.FloatField(null=True, blank=True)
    key_topics = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"Meeting with {self.employee.name} on {self.date}"
