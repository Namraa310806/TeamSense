from django.urls import path, include

urlpatterns = [
    path('employees/', include('employees.urls')),
    path('meetings/', include('meetings.urls')),
    path('', include('analytics.urls')),
    path('ai/', include('ai_engine.urls')),
    path('accounts/', include('accounts.urls')),
]
