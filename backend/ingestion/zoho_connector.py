import requests
import json
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from .models import Feedback
from employees.models import Employee
from ai_engine.sentiment import analyze_sentiment


ZOHO_CONFIG = {
    'client_id': '1000.IWODHOTGDFG94MSNMF0G75QX8YE77V',
    'client_secret': '3530ff12f3ca2142525ba2fc54faaa2cee0b3f2871',
    'token_url': 'https://accounts.zoho.com/oauth/v2/token',
    'scope': 'ZohoPeople.employees.READ ZohoPeople.forms.READ',
    'redirect_uri': 'http://localhost:8000/callback/',  # Your redirect
}

class ZohoOAuth:
    @staticmethod
    def get_token(code=None):
        data = {
            'grant_type': 'authorization_code',
            'client_id': ZOHO_CONFIG['client_id'],
            'client_secret': ZOHO_CONFIG['client_secret'],
            'redirect_uri': ZOHO_CONFIG['redirect_uri'],
        }
        if code:
            data['code'] = code
        resp = requests.post(ZOHO_CONFIG['token_url'], data=data)
        return resp.json()

    @staticmethod
    def refresh_token(refresh_token):
        data = {
            'grant_type': 'refresh_token',
            'client_id': ZOHO_CONFIG['client_id'],
            'client_secret': ZOHO_CONFIG['client_secret'],
            'refresh_token': refresh_token,
        }
        resp = requests.post(ZOHO_CONFIG['token_url'], data=data)
        return resp.json()


@shared_task
def ingest_zoho_data(access_token):
    # Employees
    headers = {
        'Authorization': f'Zoho-oauthtoken {access_token}',
    }
    
    # Get employees
    emp_resp = requests.get('https://people.zoho.com/people/api/forms/F_123456789/records', headers=headers)  # Replace F_... with your form ID
    
    employees = emp_resp.json().get('response', {}).get('request_params', {}).get('formulas', {}).get('formulas', [])
    
    for emp in employees:
        emp_id = emp.get('Employee_ID')
        if emp_id:
            employee, _ = Employee.objects.get_or_create(
                id=emp_id,
                defaults={
                    'name': f"{emp.get('First_Name')} {emp.get('Last_Name')}",
                    'department': emp.get('Department'),
                    'email': emp.get('Work_Email'),
                }
            )
            
            # Feedback/Notes (customize)
            content = emp.get('Recent_Feedback', emp.get('Notes', ''))
            if content:
                sentiment = analyze_sentiment(content)
                Feedback.objects.create(
                    employee=employee,
                    source='zoho_people',
                    content=content,
                    sentiment=sentiment,
                    timestamp=timezone.now(),
                    raw_data=emp
                )
    
    return f'Ingested Zoho People data for {len(employees)} employees'


# Management command
# python manage.py ingest_zoho ACCESS_TOKEN
