from django.core.management.base import BaseCommand
from meetings.models import Meeting
from ai_services.summarization_service import SummarizationService

class Command(BaseCommand):
    help = 'Generate and store summaries for all meeting transcripts.'

    def handle(self, *args, **options):
        summarizer = SummarizationService()
        count = 0
        for meeting in Meeting.objects.all():
            if not meeting.transcript:
                continue
            summary = summarizer.summarize(meeting.transcript)
            meeting.summary = summary
            meeting.save()
            count += 1
        self.stdout.write(self.style.SUCCESS(f'Generated summaries for {count} meetings.'))
