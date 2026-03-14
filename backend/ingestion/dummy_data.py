from django.core.management.base import BaseCommand
from ingestion.models import Feedback
from employees.models import Employee
from ingestion.tasks import process_feedback_sentiment

class Command(BaseCommand):
    help = 'Populate dummy Zoho/Slack/Forms data'

    def handle(self, *args, **options):
        # Dummy Zoho employee
        emp, _ = Employee.objects.get_or_create(id=999, defaults={'name': 'Zoho User', 'department': 'HR'})
        
        # Zoho feedback
        Feedback.objects.create(
            employee=emp,
            source='zoho_people',
            content='Excellent performance review, promoted to senior developer.',
            timestamp='2024-10-01T10:00:00Z',
            raw_data={'employee_id': 999, 'review_score': 4.8}
        )
        
        # Slack dummy
        emp2, _ = Employee.objects.get_or_create(id=998, defaults={'name': 'Slack Bot', 'department': 'Engineering'})
        Feedback.objects.create(
            employee=emp2,
            source='slack',
            content='#hr-channel Great team sync, John is leading well!',
            timestamp='2024-10-02T14:30:00Z',
            raw_data={'channel': '#hr', 'user': 'alice'}
        )
        
        # Google Forms dummy
        emp3, _ = Employee.objects.get_or_create(id=997, defaults={'name': 'Form Respondent', 'department': 'Sales'})
        Feedback.objects.create(
            employee=emp3,
            source='google_forms',
            content='Weekly survey: Manager is supportive, room for growth.',
            timestamp='2024-10-03T09:15:00Z',
            raw_data={'form_id': '123', 'question': 'Manager feedback'}
        )
        
        self.stdout.write(self.style.SUCCESS('Dummy data populated. Run process_feedback_sentiment for AI.'))

