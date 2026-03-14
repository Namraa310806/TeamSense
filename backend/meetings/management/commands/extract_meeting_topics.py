from django.core.management.base import BaseCommand
from meetings.models import Meeting
from ai_services.topic_service import TopicService

class Command(BaseCommand):
    help = 'Extract and store key topics for all meeting transcripts.'

    def handle(self, *args, **options):
        topic_extractor = TopicService()
        count = 0
        for meeting in Meeting.objects.all():
            if not meeting.transcript:
                continue
            topics = topic_extractor.extract_topics(meeting.transcript)
            meeting.key_topics = topics
            meeting.save()
            count += 1
        self.stdout.write(self.style.SUCCESS(f'Extracted topics for {count} meetings.'))
