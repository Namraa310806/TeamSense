from django.db import models


class Employee(models.Model):
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=255)
    department = models.CharField(max_length=255)
    join_date = models.DateField()
    manager = models.CharField(max_length=255, blank=True, default='')
    email = models.EmailField(unique=True, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.role} ({self.department})"
