from django.contrib import admin
from .models import EmployeeInsight, MeetingEmbedding

@admin.register(EmployeeInsight)
class EmployeeInsightAdmin(admin.ModelAdmin):
    list_display = ('employee', 'burnout_risk', 'updated_at')
    list_filter = ('burnout_risk',)

@admin.register(MeetingEmbedding)
class MeetingEmbeddingAdmin(admin.ModelAdmin):
    list_display = ('meeting', 'created_at')
