from rest_framework import serializers
from .models import Politician, ResearchResult

class ResearchResultSerializer(serializers.ModelSerializer):
    """Serializer for ResearchResult model"""
    politician_image = serializers.SerializerMethodField()
    politician_party = serializers.SerializerMethodField()
    
    class Meta:
        model = ResearchResult
        fields = [
            'id', 'position', 'background', 'accomplishments', 
            'criticisms', 'summary', 'sources', 'created_at', 'updated_at', 
            'politician_image', 'politician_party'
        ]

    def get_politician_image(self, obj):
        """Get the image URL for the politician"""
        return obj.politician.image_url if obj.politician.image_url else None

    def get_politician_party(self, obj):
        """Get the party for the politician"""
        return obj.politician.party if obj.politician.party else None

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