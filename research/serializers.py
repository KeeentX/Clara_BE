# In research/serializers.py
from rest_framework import serializers
from .models import Politician, ResearchResult

class PoliticianSerializer(serializers.ModelSerializer):
    class Meta:
        model = Politician
        fields = ['id', 'name', 'position']

class ResearchResultSerializer(serializers.ModelSerializer):
    politician = PoliticianSerializer()
    
    class Meta:
        model = ResearchResult
        fields = ['id', 'politician', 'background', 'accomplishments', 'criticisms', 'summary', 'sources', 'created_at']