from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Organization, Profile, HRUser
from .serializers import OrganizationSerializer, ProfileSerializer, HRUserSerializer
from .permissions import IsAdmin, IsExecutive, IsHR, IsCHR
from django.contrib.auth import get_user_model
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password


# Admin email whitelist
ADMIN_EMAILS = {
    'rutvigsolanki8080@gmail.com',
    'jnetri1001@gmail.com',
    'rathodvarshil9@gmail.com',
    'animeshb26526@gmail.com',
    'patelnamraa88@gmail.com',
}

User = get_user_model()


def normalize_role(role: str) -> str:
    role_value = (role or '').strip().upper()
    if role_value in {'ADMIN', 'HR', 'EMPLOYEE', 'CHR', 'EXECUTIVE'}:
        return role_value
    return 'EMPLOYEE'


def detect_role(email: str):
    """Return role for login. In hackathon mode, any valid email is accepted."""
    email_lower = email.strip().lower()
    if email_lower in ADMIN_EMAILS:
        return 'ADMIN'
    if email_lower.endswith('@chr.ac.in'):
        return 'CHR'
    if email_lower.endswith('@hr.ac.in'):
        return 'HR'
    # Default all other users to employee role (mapped to HR permissions profile).
    return 'EMPLOYEE'


def _build_auth_response(user, role: str):
    refresh = RefreshToken.for_user(user)
    token = str(refresh.access_token)
    display_name = user.first_name or user.username
    return {
        'id': user.id,
        'name': display_name,
        'email': user.email,
        'role': role,
        'token': token,
        'goal': 'Access dashboard and employee meeting intelligence insights.',
    }


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

    # HR users must be registered in the HRUser table by a CHR admin
    if role == 'HR':
        if not HRUser.objects.filter(email=email).exists():
            return Response(
                {'error': 'HR user not registered. Please contact CHR.'},
                status=status.HTTP_403_FORBIDDEN,
            )

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

    # Hackathon-safe default: attach first organization when user has none.
    if profile.organization_id is None:
        default_org = Organization.objects.order_by('id').first()
        if default_org is not None:
            profile.organization = default_org
            profile.save(update_fields=['organization'])

    return Response(_build_auth_response(user, role), status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    """POST /api/auth/register/ and /api/accounts/register/."""
    name = (request.data.get('name') or '').strip()
    email = (request.data.get('email') or '').strip().lower()
    password = request.data.get('password', '')
    role_input = request.data.get('role', 'HR')
    department = (request.data.get('department') or '').strip()

    if not name:
        return Response({'error': 'Name is required.'}, status=status.HTTP_400_BAD_REQUEST)
    if not email:
        return Response({'error': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        validate_email(email)
    except ValidationError:
        return Response({'error': 'Please enter a valid email address.'}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=email).exists():
        return Response({'error': 'A user with this email already exists.'}, status=status.HTTP_409_CONFLICT)

    try:
        validate_password(password)
    except ValidationError as exc:
        return Response({'error': ' '.join(exc.messages)}, status=status.HTTP_400_BAD_REQUEST)

    role = normalize_role(role_input)
    user = User.objects.create_user(
        username=email,
        email=email,
        first_name=name,
        password=password,
        is_active=True,
    )
    profile, _ = Profile.objects.get_or_create(user=user)
    profile.role = role
    if department:
        profile.department = department
    if profile.organization_id is None:
        default_org = Organization.objects.order_by('id').first()
        if default_org is not None:
            profile.organization = default_org
    profile.save()

    return Response(_build_auth_response(user, role), status=status.HTTP_201_CREATED)


# ---------------------------------------------------------------------------
# HR User Management – CHR only
# ---------------------------------------------------------------------------

@api_view(['GET', 'POST'])
@permission_classes([IsCHR])
def hr_users_list_create(request):
    """
    GET  /api/accounts/hr-users/  → list all HR users
    POST /api/accounts/hr-users/  → add a new HR user
    """
    if request.method == 'GET':
        hr_users = HRUser.objects.all()
        serializer = HRUserSerializer(hr_users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # POST
    serializer = HRUserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsCHR])
def hr_user_delete(request, pk):
    """
    DELETE /api/accounts/hr-users/<pk>/  → delete an HR user by id
    """
    try:
        hr_user = HRUser.objects.get(pk=pk)
    except HRUser.DoesNotExist:
        return Response({'error': 'HR user not found.'}, status=status.HTTP_404_NOT_FOUND)
    hr_user.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Organisation ViewSet
# ---------------------------------------------------------------------------

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
