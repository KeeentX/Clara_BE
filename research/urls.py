from django.urls import path
from . import views

urlpatterns = [
    path('research/<str:name>/', views.research_politician, name='research_politician'),
    path('research/report/<int:report_id>/', views.get_research_report, name='get_research_report'),

    # endpoint for politicians
    path('politicians/', views.get_politicians, name='get_politicians'),
    path('politicians/<int:politician_id>/', views.get_politician, name='get_politician'),
]