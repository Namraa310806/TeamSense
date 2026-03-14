from django.core.management.base import BaseCommand
from meetings.models import Meeting
from analytics.models import MeetingEmbedding
from ai_services.embedding_service import EmbeddingService

class Command(BaseCommand):
    help = 'Generate and store embeddings for all meeting transcripts.'

    def handle(self, *args, **options):
        embedder = EmbeddingService()
        count = 0
        for meeting in Meeting.objects.all():
            if not meeting.transcript:
                continue
            embedding = embedder.embed_text(meeting.transcript)
            MeetingEmbedding.objects.update_or_create(
                meeting=meeting,
                defaults={'embedding': embedding}
            )
            count += 1
        self.stdout.write(self.style.SUCCESS(f'Generated embeddings for {count} meetings.'))
