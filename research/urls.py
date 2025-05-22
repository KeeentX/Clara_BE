from django.urls import path
from . import views

urlpatterns = [
    path('research/<str:name>/', views.research_politician, name='research_politician'),
    path('chats/', views.chat_list, name='chat-list'),
    path('chats/<int:pk>/', views.chat_detail, name='chat-detail'),
    path('chats/<int:chat_id>/messages/', views.add_message, name='add-message'),
    path('chats/clear/', views.clear_all_chats, name='clear-all-chats'),
]