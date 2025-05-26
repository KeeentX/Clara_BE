from django.urls import path
from . import views

urlpatterns = [
    # Chat endpoints
    path('chats/', views.ChatView.as_view(), name='chat_list_create'),
    path('chats/<int:chat_id>/', views.ChatDetailView.as_view(), name='chat_detail'),
    path('temporary-chats/<int:chat_id>/', views.TemporaryChatView.as_view(), name='temporary_chat_detail'),

    # Question endpoints
    path('questions/', views.QuestionView.as_view(), name='question_create'),
    path('chats/<int:chat_id>/qanda/', views.ChatQandAView.as_view(), name='chat_qanda'),
]
