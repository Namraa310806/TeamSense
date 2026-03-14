from django.db import models
from django.contrib.auth.models import User
import uuid


class Organization(models.Model):
    organization_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    organization_name = models.CharField(max_length=255)
    industry = models.CharField(max_length=255, blank=True, default='')
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='created_organizations')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["organization_name"]

    def __str__(self):
        return self.organization_name


class Profile(models.Model):
    ROLE_CHOICES = (
        ('ADMIN', 'Admin'),
        ('EXECUTIVE', 'Executive'),
        ('HR', 'HR'),
        ('CHR', 'CHR'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='HR')
    organization = models.ForeignKey(Organization, null=True, blank=True, on_delete=models.SET_NULL, related_name='members')
    designation = models.CharField(max_length=255, blank=True, default='')
    department = models.CharField(max_length=255, blank=True, default='')

    def __str__(self):
        return f"{self.user.username} - {self.role}"


class HRUser(models.Model):
    """HR users that are registered by CHR and allowed to log in."""
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True, db_index=True)
    role = models.CharField(max_length=10, default='HR')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.email})"


# Signal to create profile on user creation
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        instance.profile.save()
    except Exception:
        pass
