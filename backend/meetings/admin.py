from django.contrib import admin
from .models import Meeting

@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ('employee', 'date', 'sentiment_score')
    list_filter = ('date', 'employee__department')
    search_fields = ('employee__name', 'transcript', 'summary')
