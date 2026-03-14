from django.core.management.base import BaseCommand
from meetings.models import Meeting
from ai_services.sentiment_service import SentimentService

class Command(BaseCommand):
    help = 'Analyze and store sentiment for all meeting transcripts.'

    def handle(self, *args, **options):
        sentiment_analyzer = SentimentService()
        count = 0
        for meeting in Meeting.objects.all():
            if not meeting.transcript:
                continue
            result = sentiment_analyzer.analyze(meeting.transcript)
            # Store sentiment as a score: positive=1, neutral=0, negative=-1
            label = result['label']
            score = {'positive': 1, 'neutral': 0, 'negative': -1}[label]
            meeting.sentiment_score = score
            meeting.save()
            count += 1
        self.stdout.write(self.style.SUCCESS(f'Analyzed sentiment for {count} meetings.'))
