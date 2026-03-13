from django.contrib import admin
from .models import Employee

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('name', 'role', 'department', 'join_date', 'manager')
    list_filter = ('department',)
    search_fields = ('name', 'role', 'department')
