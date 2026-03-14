from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.role == 'ADMIN')

class IsExecutive(BasePermission):
    def has_permission(self, request, view):
        return hasattr(request.user, 'profile') and request.user.profile.role == 'EXECUTIVE'

class IsHR(BasePermission):
    def has_permission(self, request, view):
        return hasattr(request.user, 'profile') and request.user.profile.role == 'HR'

class IsSameOrganization(BasePermission):
    def has_object_permission(self, request, view, obj):
        if hasattr(request.user, 'profile') and request.user.profile.organization:
            return obj.organization == request.user.profile.organization
        return False
