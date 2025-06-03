from rest_framework import serializers
from .models import Chat, QandA
from research.serializers import ResearchResultSerializer
from research.models import Politician

class QandASerializer(serializers.ModelSerializer):
    class Meta:
        model = QandA
        fields = ['id', 'chat', 'question', 'answer', 'created_at']
        read_only_fields = ['id', 'created_at']

class ChatSerializer(serializers.ModelSerializer):
    politician_image = serializers.SerializerMethodField()
    politician_party = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = ['id', 'politician', 'politician_image', 'politician_party', 'user', 'created_at', 'updated_at', 'research_report']
        read_only_fields = ['id', 'created_at', 'updated_at', 'user']

    def get_politician_image(self, obj):
        """Get the image URL for the politician by name lookup"""
        try:
            politician = Politician.objects.get(name__iexact=obj.politician)
            return politician.image_url
        except Politician.DoesNotExist:
            return None

    def get_politician_party(self, obj):
        """Get the party for the politician by name lookup"""
        try:
            politician = Politician.objects.get(name__iexact=obj.politician)
            return politician.party
        except Politician.DoesNotExist:
            return None
