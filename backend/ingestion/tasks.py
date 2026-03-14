from celery import shared_task
from .models import Feedback
from employees.models import Employee
from ai_engine.sentiment import analyze_sentiment
from django.core.files.storage import default_storage
import pandas as pd
from .zoho_connector import ingest_zoho_data  # Zoho task

@shared_task
def parse_csv_task(file_path, employee_ids=None):
    try:
        df = pd.read_csv(file_path)
        for _, row in df.iterrows():
            employee_id = row.get('employee_id') or row.get('id')
            if employee_id:
                employee, _ = Employee.objects.get_or_create(
                    id=employee_id,
                    defaults={'name': row.get('name', 'Unknown'), 'department': row.get('department', 'General')}
                )
                content = str(row.get('feedback', row.to_dict()))
                sentiment = analyze_sentiment(content)
                Feedback.objects.create(
                    employee=employee,
                    source='csv',
                    content=content,
                    sentiment=sentiment,
                    timestamp=pd.to_datetime(row.get('timestamp', timezone.now())),
                    raw_data=row.to_dict()
                )
        default_storage.delete(file_path)
    except Exception as e:
        print(f"CSV error: {e}")

@shared_task
def process_feedback_sentiment(feedback_id):
    feedback = Feedback.objects.get(id=feedback_id)
    score = analyze_sentiment(feedback.content)
    feedback.sentiment = score
    feedback.save()

# Zoho
ingest_zoho_task = ingest_zoho_data
