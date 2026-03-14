import gspread
from google.oauth2.service_account import Credentials
from celery import shared_task
from django.conf import settings
from .models import Feedback
from employees.models import Employee
from ai_engine.sentiment import analyze_sentiment

@shared_task
def ingest_google_forms(form_id='your_form_id'):
    gc = gspread.service_account(filename=settings.GOOGLE_SERVICE_ACCOUNT)
    sheet = gc.open_by_key(form_id).sheet1
    
    rows = sheet.get_all_records()
    
    for row in rows:
        emp_email = row.get('Email')
        if emp_email:
            emp, _ = Employee.objects.get_or_create(email=emp_email, defaults={'name': row.get('Name', 'Unknown')})
            
            feedback = row.get('Feedback', '')
            sentiment = analyze_sentiment(feedback)
            Feedback.objects.create(
                employee=emp,
                source='google_forms',
                content=feedback,
                sentiment=sentiment,
                timestamp=row.get('Timestamp'),
                raw_data=row
            )
    
    return 'Google Forms data ingested'
