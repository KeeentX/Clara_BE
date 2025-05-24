from django.urls import path
from . import views

urlpatterns = [
    path('research/<str:name>/', views.research_politician, name='research_politician'),
    path('research/report/<int:report_id>/', views.get_research_report, name='get_research_report'),
]