from django.urls import path
from . import views

urlpatterns = [
    path('research/<str:name>/', views.research_politician, name='research_politician'),
]