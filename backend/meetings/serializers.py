from rest_framework import serializers
from .models import Meeting


class MeetingSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.name', read_only=True)

    class Meta:
        model = Meeting
        fields = '__all__'


class MeetingUploadSerializer(serializers.Serializer):
    employee_id = serializers.IntegerField()
    transcript = serializers.CharField()
    date = serializers.DateField(required=False)
