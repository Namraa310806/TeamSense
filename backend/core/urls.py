from django.urls import path, include
from accounts.views import login_view

urlpatterns = [
    path('login/', login_view, name='login-fallback'),
    path('employees/', include('employees.urls')),
    path('meetings/', include('meetings.urls')),
    path('', include('analytics.urls')),
    path('ai/', include('ai_engine.urls')),
    path('accounts/', include('accounts.urls')),
]
