from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Meeting
from .tasks import update_attrition_task


@receiver(post_save, sender=Meeting)
def on_meeting_save(sender, instance, **kwargs):
    """Trigger attrition recalc if sentiment_score updated."""
    if instance.sentiment_score is not None and kwargs.get('update_fields', {}).intersection({'sentiment_score'}):
        update_attrition_task.delay(instance.employee_id)

