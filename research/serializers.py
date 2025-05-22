# In research/serializers.py
from rest_framework import serializers
from .models import Politician, ResearchResult, Chat, Message

class PoliticianSerializer(serializers.ModelSerializer):
    class Meta:
        model = Politician
        fields = ['id', 'name', 'position', 'image_url', 'created_at']

class ResearchResultSerializer(serializers.ModelSerializer):
    politician = PoliticianSerializer()
    
    class Meta:
        model = ResearchResult
        fields = ['id', 'politician', 'background', 'accomplishments', 'criticisms', 'summary', 'sources', 'created_at']

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'content', 'role', 'timestamp']

class ChatListSerializer(serializers.ModelSerializer):
    message_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Chat
        fields = ['id', 'title', 'created_at', 'updated_at', 'message_count']
    
    def get_message_count(self, obj):
        return obj.messages.count()

class ChatDetailSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    
    class Meta:
        model = Chat
        fields = ['id', 'title', 'created_at', 'updated_at', 'messages']