from rest_framework import serializers
from .models import (
    EmployeeMeetingInsight,
    Meeting,
    MeetingSpeakerMapping,
    MeetingTranscript,
)


class MeetingSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.name', read_only=True)
    participant_ids = serializers.SerializerMethodField()
    participant_names = serializers.SerializerMethodField()
    organization_name = serializers.CharField(source='organization.organization_name', read_only=True)

    def get_participant_ids(self, obj):
        return [p.employee_id for p in obj.participants.select_related('employee').all()]

    def get_participant_names(self, obj):
        return [p.employee.name for p in obj.participants.select_related('employee').all()]

    class Meta:
        model = Meeting
        fields = [
            'id',
            'organization',
            'organization_name',
            'meeting_title',
            'department',
            'meeting_date',
            'uploaded_by',
            'meeting_file',
            'transcript_status',
            'employee',
            'employee_name',
            'participant_ids',
            'participant_names',
            'date',
            'transcript',
            'summary',
            'sentiment_score',
            'key_topics',
            'created_at',
            'updated_at',
        ]


class MeetingTranscriptSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeetingTranscript
        fields = ['id', 'meeting', 'speaker', 'text', 'start_time', 'end_time', 'created_at']


class MeetingSpeakerMappingSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.name', read_only=True)

    class Meta:
        model = MeetingSpeakerMapping
        fields = ['id', 'meeting', 'speaker_label', 'employee', 'employee_name', 'created_at', 'updated_at']


class EmployeeMeetingInsightSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.name', read_only=True)

    class Meta:
        model = EmployeeMeetingInsight
        fields = [
            'id',
            'employee',
            'employee_name',
            'meeting',
            'participation_duration',
            'sentiment_score',
            'engagement_score',
            'speaking_turns',
            'interruption_signals',
            'created_at',
            'updated_at',
        ]


class MeetingUploadSerializer(serializers.Serializer):
    organization_id = serializers.IntegerField(required=False)
    meeting_title = serializers.CharField(required=False, allow_blank=True, default='')
    department = serializers.CharField(required=False, allow_blank=True, default='')
    meeting_date = serializers.DateField(required=False)
    participants = serializers.JSONField(required=False)
    meeting_file = serializers.FileField(required=False)
    transcript = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        participants = attrs.get('participants')
        if participants is None or not isinstance(participants, list) or len(participants) == 0:
            raise serializers.ValidationError('participants must be a non-empty list of employee IDs.')

        if attrs.get('meeting_file') is None and not attrs.get('transcript'):
            raise serializers.ValidationError('Provide either meeting_file or transcript.')

        if attrs.get('meeting_file') is not None:
            filename = attrs['meeting_file'].name.lower()
            if not (filename.endswith('.mp3') or filename.endswith('.wav') or filename.endswith('.mp4')):
                raise serializers.ValidationError('meeting_file must be mp3, wav, or mp4.')

        return attrs


class RecordingUploadSerializer(serializers.Serializer):
    employee_id = serializers.IntegerField(required=False)
    employee_ids = serializers.JSONField(required=False)
    recording = serializers.FileField()
    date = serializers.DateField(required=False)
    speaker_turns = serializers.JSONField(required=False)

    def validate(self, attrs):
        employee_id = attrs.get('employee_id')
        employee_ids = attrs.get('employee_ids')
        if employee_ids is None and employee_id is None:
            raise serializers.ValidationError('Provide employee_id or employee_ids.')
        if employee_ids is not None and not isinstance(employee_ids, list):
            raise serializers.ValidationError('employee_ids must be a list of integers.')
        return attrs


class MapSpeakersSerializer(serializers.Serializer):
    meeting_id = serializers.IntegerField()
    speaker_mapping = serializers.DictField(
        child=serializers.IntegerField(allow_null=True),
        help_text='Mapping of speaker labels to employee IDs. Example: {"Speaker_1": 3}',
    )
