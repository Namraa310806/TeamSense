from django.db import models
from django.conf import settings
from accounts.models import Organization
from django.contrib.auth.models import User


class Employee(models.Model):
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=255)
    department = models.CharField(max_length=255)
    join_date = models.DateField()
    # New relations for multi-organization support
    organization = models.ForeignKey(Organization, null=True, blank=True, on_delete=models.SET_NULL, related_name='employees')
    # manager can be either a string (legacy) or a FK to a User
    manager = models.CharField(max_length=255, blank=True, default='')
    manager_user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='manages')
    hr_owner = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='hr_owned_employees')
    email = models.EmailField(unique=True, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.role} ({self.department})"
