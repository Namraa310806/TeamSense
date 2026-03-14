from django.core.management.base import BaseCommand
from ingestion.zoho_connector import ingest_zoho_data

class Command(BaseCommand):
    help = 'Ingest from Zoho People HRMS'

    def add_arguments(self, parser):
        parser.add_argument('access_token', type=str)

    def handle(self, *args, **options):
        result = ingest_zoho_data.delay(options['access_token'])
        self.stdout.write(
            self.style.SUCCESS(f'Zoho ingestion queued. Task ID: {result.id}')
        )

