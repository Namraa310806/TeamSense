from django.urls import path
from . import views

urlpatterns = [
    path('query/', views.ai_query, name='ai-query'),
    path('semantic-search/', views.SemanticSearchAPI.as_view(), name='semantic-search'),
    path('hr-assistant/', views.hr_assistant, name='hr-assistant'),
]
