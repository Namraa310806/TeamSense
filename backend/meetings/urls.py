from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_meeting, name='meeting-upload'),
    path('', views.meeting_list, name='meeting-list'),
    path('<int:pk>/', views.meeting_detail, name='meeting-detail'),
]
