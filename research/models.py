from django.db import models
from django.utils import timezone

class Politician(models.Model):
    """
    Stores basic information about a politician.
    One politician can have multiple research results (historical analyses).
    """
    name = models.CharField(max_length=200)
    image_url = models.URLField(blank=True, null=True)
    party = models.CharField(max_length=200, blank=True)
    bio = models.TextField(blank=True)
    issues = models.TextField(blank=True)  # Changed from JSONField to TextField
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['name']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.created_at.strftime('%Y-%m-%d')})"
    
    def get_latest_research(self):
        """Get the most recent research for this politician"""
        return self.research_results.order_by('-created_at').first()

class ResearchResult(models.Model):
    """
    Stores the analysis results for a politician.
    Each result belongs to exactly one politician.
    """
    politician = models.ForeignKey(Politician, on_delete=models.CASCADE, related_name='research_results')
    position = models.CharField(max_length=200)
    background = models.TextField(blank=True)
    accomplishments = models.TextField(blank=True)  
    criticisms = models.TextField(blank=True)
    summary = models.TextField(blank=True)
    sources = models.JSONField(default=dict)  # Store source URLs and metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['politician', '-created_at']),
            models.Index(fields=['position']),
        ]
    
    def __str__(self):
        return f"Research on {self.politician.name} ({self.position}) ({self.created_at.strftime('%Y-%m-%d')})"
    
    def is_recent(self, days=7):
        """Check if this research is recent (within the specified number of days)"""
        return (timezone.now() - self.created_at).days <= days