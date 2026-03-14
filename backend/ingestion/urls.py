
from django.urls import path
from . import views

urlpatterns = [
    path('upload-csv/', views.upload_feedback_csv, name='upload_csv'),
    path('csv/', views.upload_feedback_csv_alias, name='upload_csv_alias'),
    path('slack/', views.ingest_slack, name='ingest_slack'),
    path('google-forms/', views.ingest_google_forms, name='ingest_google_forms'),
    path('forms/', views.ingest_google_forms_alias, name='ingest_google_forms_alias'),
    path('upload-document/', views.upload_document, name='upload_document'),
    path('document/', views.upload_document_alias, name='upload_document_alias'),
    path('feedback/', views.feedback_list, name='feedback_list'),
    path('stats/', views.ingestion_stats, name='ingestion_stats'),
    path('overview/', views.ingestion_overview, name='ingestion_overview'),
    path('jobs/', views.ingestion_jobs, name='ingestion_jobs'),
]

