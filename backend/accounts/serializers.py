from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Organization, Profile, HRUser


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ['id', 'organization_id', 'organization_name', 'industry', 'created_by', 'created_at']


class ProfileSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Profile
        fields = ['user', 'user_email', 'role', 'organization', 'designation', 'department']


class HRUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = HRUser
        fields = ['id', 'name', 'email', 'role', 'created_at']
        read_only_fields = ['id', 'role', 'created_at']
