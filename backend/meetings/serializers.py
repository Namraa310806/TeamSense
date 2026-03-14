from rest_framework import serializers
from .models import (
    EmployeeMeetingInsight,
    Meeting,
    MeetingInsight,
    MeetingSpeakerMapping,
    MeetingTranscript,
)


class MeetingSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.name', read_only=True)
    participant_ids = serializers.SerializerMethodField()
    participant_names = serializers.SerializerMethodField()
    organization_name = serializers.CharField(source='organization.organization_name', read_only=True)
    processing_status = serializers.CharField(source='transcript_status', read_only=True)
    transcript_text = serializers.CharField(source='transcript', read_only=True)
    overall_sentiment = serializers.FloatField(source='sentiment_score', read_only=True)

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
            'processing_status',
            'employee',
            'employee_name',
            'participant_ids',
            'participant_names',
            'date',
            'transcript',
            'transcript_text',
            'summary',
            'sentiment_score',
            'overall_sentiment',
            'key_topics',
            'created_at',
            'updated_at',
        ]


class MeetingTranscriptSerializer(serializers.ModelSerializer):
    speaker_employee_name = serializers.CharField(source='speaker_employee.name', read_only=True)

    class Meta:
        model = MeetingTranscript
        fields = [
            'id',
            'meeting',
            'speaker',
            'speaker_employee',
            'speaker_employee_name',
            'text',
            'start_time',
            'end_time',
            'created_at',
        ]


class MeetingInsightSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeetingInsight
        fields = ['id', 'meeting', 'insight_type', 'description', 'severity', 'created_at']


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
    transcript_text = serializers.CharField(required=False, allow_blank=True)

    ALLOWED_EXTENSIONS = {'.mp3', '.wav', '.mp4', '.m4a'}
    ALLOWED_MIME_TYPES = {
        'audio/mpeg',
        'audio/mp3',
        'audio/wav',
        'audio/x-wav',
        'audio/mp4',
        'audio/x-m4a',
        'video/mp4',
        'application/octet-stream',  # browsers may fallback to this
    }
    MAX_FILE_SIZE_BYTES = 200 * 1024 * 1024

    def _normalize_participants(self, participants):
        if participants is None:
            return []
        if isinstance(participants, str):
            raw = participants.strip()
            if not raw:
                return []
            try:
                import json
                parsed = json.loads(raw)
                participants = parsed
            except Exception:
                participants = [p.strip() for p in raw.split(',') if p.strip()]
        if not isinstance(participants, list):
            raise serializers.ValidationError('participants must be a list of employee IDs.')

        normalized = []
        for value in participants:
            try:
                normalized.append(int(value))
            except (TypeError, ValueError):
                continue
        return normalized

    def validate(self, attrs):
        participants = self._normalize_participants(attrs.get('participants'))
        attrs['participants'] = participants
        if len(participants) == 0:
            raise serializers.ValidationError('participants must be a non-empty list of employee IDs.')

        transcript = (attrs.get('transcript_text') or attrs.get('transcript') or '').strip()
        attrs['transcript'] = transcript

        if attrs.get('meeting_file') is None and not transcript:
            raise serializers.ValidationError('Provide either meeting_file or transcript_text.')

        if attrs.get('meeting_file') is not None:
            upload = attrs['meeting_file']
            filename = (upload.name or '').lower()

            import os
            _, ext = os.path.splitext(filename)
            if ext not in self.ALLOWED_EXTENSIONS:
                raise serializers.ValidationError('Invalid file format. Allowed: mp3, wav, mp4, m4a.')

            mime_type = (getattr(upload, 'content_type', '') or '').lower()
            if mime_type and mime_type not in self.ALLOWED_MIME_TYPES:
                raise serializers.ValidationError('Invalid file format (MIME type not supported).')

            size = int(getattr(upload, 'size', 0) or 0)
            if size > self.MAX_FILE_SIZE_BYTES:
                raise serializers.ValidationError('File too large. Maximum allowed size is 200MB.')

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
