from django.apps import AppConfig
from django.db.models.signals import post_migrate

def create_ingestion_commands(sender, **kwargs):
    from .management.commands import ingest_bamboohr

class IngestionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ingestion'

    def ready(self):
        post_migrate.connect(create_ingestion_commands, sender=self)

