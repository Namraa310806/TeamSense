
from django.urls import path
from . import views

urlpatterns = [
    path('upload-csv/', views.upload_feedback_csv, name='upload_csv'),
    path('feedback/', views.feedback_list, name='feedback_list'),
    path('zoho-auth/', views.zoho_auth, name='zoho_auth'),
    path('zoho-callback/', views.zoho_callback, name='zoho_callback'),
]

