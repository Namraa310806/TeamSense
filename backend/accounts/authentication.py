from rest_framework_simplejwt.authentication import JWTAuthentication

class CustomJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        user_auth_tuple = super().authenticate(request)
        if user_auth_tuple is not None:
            user, token = user_auth_tuple
            # Optionally, check user profile/role here
            return (user, token)
        return None
