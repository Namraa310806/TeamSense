from slack_sdk import WebClient
from celery import shared_task
from django.conf import settings
from .models import Feedback
from employees.models import Employee
from ai_engine.sentiment import analyze_sentiment

class SlackConnector:
    def __init__(self):
        self.client = WebClient(token=settings.SLACK_BOT_TOKEN)

@shared_task
def ingest_slack_data(channel='#hr-feedback'):
    connector = SlackConnector()
    
    # Fetch recent messages
    resp = connector.client.conversations_history(channel=channel, limit=100)
    
    for msg in resp['messages']:
        text = msg.get('text', '')
        if text:
            # Dummy employee match (extend with @mentions)
            emp_name = 'John Doe'  # Extract from mentions
            emp, _ = Employee.objects.get_or_create(name=emp_name, defaults={'department': 'Engineering'})
            
            sentiment = analyze_sentiment(text)
            Feedback.objects.create(
                employee=emp,
                source='slack',
                content=text,
                sentiment=sentiment,
                timestamp=msg.get('ts'),
                raw_data={'channel': channel, 'user': msg.get('user')}
            )
    
    return 'Slack data ingested'
