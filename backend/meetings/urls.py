from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_meeting, name='meeting-upload'),
    path('transcript/', views.meeting_transcript, name='meeting-transcript'),
    path('summary/', views.meeting_summary, name='meeting-summary'),
    path('map-speakers/', views.map_speakers, name='meeting-map-speakers'),
    path('<int:meeting_id>/insights/', views.meeting_insights, name='meeting-insights'),
    path('upload-recording/', views.upload_meeting_recording, name='meeting-upload-recording'),
    path('analysis/<int:meeting_id>/', views.meeting_analysis_detail, name='meeting-analysis-detail'),
    path('analysis/employee/<int:employee_id>/', views.employee_meeting_insights, name='employee-meeting-insights'),
    path('', views.meeting_list, name='meeting-list'),
    path('<int:pk>/', views.meeting_detail, name='meeting-detail'),
]
