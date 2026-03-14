from django.contrib import admin
from .models import EmployeeMeetingInsight, Meeting, MeetingSpeakerMapping, MeetingTranscript

@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ('meeting_title', 'employee', 'organization', 'meeting_date', 'transcript_status', 'sentiment_score')
    list_filter = ('transcript_status', 'meeting_date', 'employee__department', 'organization')
    search_fields = ('meeting_title', 'employee__name', 'transcript', 'summary')


@admin.register(MeetingTranscript)
class MeetingTranscriptAdmin(admin.ModelAdmin):
    list_display = ('meeting', 'speaker', 'start_time', 'end_time')
    list_filter = ('speaker',)
    search_fields = ('speaker', 'text')


@admin.register(MeetingSpeakerMapping)
class MeetingSpeakerMappingAdmin(admin.ModelAdmin):
    list_display = ('meeting', 'speaker_label', 'employee', 'updated_at')
    search_fields = ('speaker_label', 'employee__name')


@admin.register(EmployeeMeetingInsight)
class EmployeeMeetingInsightAdmin(admin.ModelAdmin):
    list_display = ('employee', 'meeting', 'engagement_score', 'sentiment_score', 'speaking_turns')
    list_filter = ('employee__department',)
