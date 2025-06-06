from django.urls import path
from .views import RegisterView, LoginView, AnonymousTokenView
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/anonymous/', AnonymousTokenView.as_view(), name='anonymous_token'),
    path('politicians/add/<int:politician_id>/', views.add_politician, name='add_politician'),
    path('politicians/remove/<int:politician_id>/', views.remove_politician, name='remove_politician'),
    path('politicians/picks/', views.get_picks, name='get_my_picks'),
    path('politicians/picks/<int:user_id>/', views.get_picks, name='get_user_picks'),
]
