from rest_framework import serializers
from .models import Chat, QandA
from research.serializers import ResearchResultSerializer

class QandASerializer(serializers.ModelSerializer):
    class Meta:
        model = QandA
        fields = ['id', 'chat', 'question', 'answer', 'created_at']
        read_only_fields = ['id', 'created_at']

class ChatSerializer(serializers.ModelSerializer):
    qanda_set = QandASerializer(many=True, read_only=True)
    
    class Meta:
        model = Chat
        fields = ['id', 'politician', 'user', 'created_at', 'research_report', 'qanda_set']
        read_only_fields = ['id', 'created_at', 'user']