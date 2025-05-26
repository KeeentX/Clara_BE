from rest_framework import serializers
from .models import Chat, QandA
from research.serializers import ResearchResultSerializer

class QandASerializer(serializers.ModelSerializer):
    class Meta:
        model = QandA
        fields = ['id', 'chat', 'question', 'answer', 'created_at']
        read_only_fields = ['id', 'created_at']

class ChatSerializer(serializers.ModelSerializer):

    class Meta:
        model = Chat
        fields = ['id', 'politician', 'user', 'created_at', 'updated_at', 'research_report']
        read_only_fields = ['id', 'created_at', 'updated_at', 'user']
