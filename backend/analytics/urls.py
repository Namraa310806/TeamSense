from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('employee-insights/<int:employee_id>/', views.employee_insights, name='employee-insights'),
    path('attrition/<int:employee_id>/', views.attrition_risk, name='attrition-risk'),
]
