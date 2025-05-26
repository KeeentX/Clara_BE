from django.urls import path
from .views import RegisterView, LoginView, AnonymousTokenView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/anonymous/', AnonymousTokenView.as_view(), name='anonymous_token'),
]
