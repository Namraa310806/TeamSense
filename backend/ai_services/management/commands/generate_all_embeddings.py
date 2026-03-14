from django.core.management.base import BaseCommand
from meetings.models import Meeting
from analytics.models import EmployeeInsight
from ai_services.embedding_service import EmbeddingService
from ai_services.vector_store import FaissVectorStore
import os

EMBEDDING_DIM = 384
VECTOR_INDEX_PATH = 'faiss.index'
META_PATH = 'faiss_meta.pkl'

class Command(BaseCommand):
    help = 'Generate embeddings for meetings, summaries, and HR notes (EmployeeInsight.concerns) for semantic search.'

    def handle(self, *args, **options):
        embedder = EmbeddingService()
        vector_store = FaissVectorStore(dim=EMBEDDING_DIM, index_path=VECTOR_INDEX_PATH, meta_path=META_PATH)
        vectors = []
        meta = []
        # Meeting transcripts
        for meeting in Meeting.objects.all():
            if meeting.transcript:
                vectors.append(embedder.embed_text(meeting.transcript))
                meta.append({'type': 'meeting_transcript', 'id': meeting.id, 'text': meeting.transcript})
            if meeting.summary:
                vectors.append(embedder.embed_text(meeting.summary))
                meta.append({'type': 'meeting_summary', 'id': meeting.id, 'text': meeting.summary})
        # EmployeeInsight concerns (HR notes/feedback)
        for insight in EmployeeInsight.objects.all():
            if insight.concerns:
                vectors.append(embedder.embed_text(insight.concerns))
                meta.append({'type': 'hr_note', 'id': insight.id, 'employee_id': insight.employee_id, 'text': insight.concerns})
        vector_store.add(vectors, meta)
        self.stdout.write(self.style.SUCCESS(f'Generated {len(vectors)} embeddings for semantic search.'))
