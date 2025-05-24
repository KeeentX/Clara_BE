from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User

def get_user_from_token(request):
    """Extract user from JWT token if present"""
    auth_header = request.META.get('HTTP_AUTHORIZATION', None)
    if not auth_header:
        return None
    try:
        # Extract the token
        if ' ' in auth_header:
            prefix, token = auth_header.split(' ', 1)
        else:
            token = auth_header

        # Verify and decode the token
        refresh = RefreshToken(token)
        user_id = refresh.payload.get('user_id')
        if user_id:
            return User.objects.get(id=user_id)
        return None
    except Exception:
        return None

