from rest_framework import serializers
from .models import Politician, ResearchResult

class ResearchResultSerializer(serializers.ModelSerializer):
    """Serializer for ResearchResult model"""
    
    class Meta:
        model = ResearchResult
        fields = [
            'id', 'position', 'background', 'accomplishments', 
            'criticisms', 'summary', 'sources', 'created_at', 'updated_at'
        ]

class PoliticianSerializer(serializers.ModelSerializer):
    """Serializer for Politician model"""
    
    # Include the latest research result as a nested serializer
    latest_research = serializers.SerializerMethodField()
    
    class Meta:
        model = Politician
        fields = ['id', 'name', 'image_url', 'created_at', 'latest_research']
    
    def get_latest_research(self, obj):
        """Get the latest research for this politician"""
        latest = obj.get_latest_research()
        if latest:
            return ResearchResultSerializer(latest).data
        return None