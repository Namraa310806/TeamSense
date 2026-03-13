from django.core.management.base import BaseCommand
from meetings.models import Meeting
from ai_services.ner_service import NERService
import json

class Command(BaseCommand):
    help = 'Extract and store named entities for all meeting transcripts.'

    def handle(self, *args, **options):
        ner = NERService()
        count = 0
        for meeting in Meeting.objects.all():
            if not meeting.transcript:
                continue
            entities = ner.extract_entities(meeting.transcript)
            # Store as JSON in summary field for demo, or add a new field/model for production
            meeting.summary = meeting.summary + '\nEntities: ' + json.dumps(entities)
            meeting.save()
            count += 1
        self.stdout.write(self.style.SUCCESS(f'Extracted entities for {count} meetings.'))
