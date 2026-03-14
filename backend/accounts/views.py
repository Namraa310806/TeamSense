from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Organization, Profile
from .serializers import OrganizationSerializer, ProfileSerializer
from .permissions import IsAdmin, IsExecutive, IsHR
from django.contrib.auth.models import User
from django.core.validators import validate_email
from django.core.exceptions import ValidationError


# Admin email whitelist
ADMIN_EMAILS = {
    'rutvigsolanki8080@gmail.com',
    'jnetri1001@gmail.com',
    'rathodvarshil9@gmail.com',
    'animeshb26526@gmail.com',
    'patelnamraa88@gmail.com',
}


def detect_role(email: str):
    """Return role for login. In hackathon mode, any valid email is accepted."""
    email_lower = email.strip().lower()
    if email_lower in ADMIN_EMAILS:
        return 'ADMIN'
    if email_lower.endswith('@hr.ac.in'):
        return 'HR'
    if email_lower.endswith('@chr.ac.in'):
        return 'CHR'
    # Hackathon mode: allow any valid email and grant dashboard access.
    return 'ADMIN'


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    POST /api/accounts/login/
    Body: { "name": str, "email": str, "password": str }
    Returns: { "name": str, "email": str, "role": str, "token": str }
    """
    name = (request.data.get('name') or '').strip()
    email = (request.data.get('email') or '').strip().lower()
    password = request.data.get('password', '')

    if not email:
        return Response({'error': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)
    if not name:
        return Response({'error': 'Name is required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        validate_email(email)
    except ValidationError:
        return Response({'error': 'Please enter a valid email address.'}, status=status.HTTP_400_BAD_REQUEST)

    role = detect_role(email)

    # Get or create the Django user keyed by email (use email as username)
    user, created = User.objects.get_or_create(
        username=email,
        defaults={'email': email, 'first_name': name},
    )
    if not created:
        # Update name if it changed
        if user.first_name != name:
            user.first_name = name
            user.save(update_fields=['first_name'])

    # Ensure the Profile exists and has the correct role
    profile, _ = Profile.objects.get_or_create(user=user)
    if profile.role != role:
        profile.role = role
        profile.save(update_fields=['role'])

    # Issue JWT
    refresh = RefreshToken.for_user(user)
    token = str(refresh.access_token)

    return Response({
        'name': name,
        'email': email,
        'role': role,
        'token': token,
        'goal': 'Access dashboard and employee meeting intelligence insights.',
    }, status=status.HTTP_200_OK)


class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer

    def get_permissions(self):
        if self.action in ['list', 'destroy']:
            return [IsAdmin()]
        elif self.action in ['create', 'update', 'partial_update']:
            return [IsAdmin() or IsExecutive()]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'profile') and user.profile.role == 'ADMIN':
            return Organization.objects.all()
        elif hasattr(user, 'profile') and user.profile.organization:
            return Organization.objects.filter(id=user.profile.organization.id)
        return Organization.objects.none()

    def perform_create(self, serializer):
        org = serializer.save(created_by=self.request.user)
        try:
            profile = self.request.user.profile
            profile.organization = org
            profile.role = 'EXECUTIVE'
            profile.save()
        except Exception:
            pass


@api_view(['GET'])
@permission_classes([IsAdmin | IsExecutive | IsHR])
def me(request):
    if hasattr(request.user, 'profile'):
        return Response(ProfileSerializer(request.user.profile).data)
    return Response({'error': 'No profile found'}, status=status.HTTP_404_NOT_FOUND)
