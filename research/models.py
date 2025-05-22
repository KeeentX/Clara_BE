from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class Politician(models.Model):
    """
    Stores basic information about a politician.
    One politician can have multiple research results (historical analyses).
    """
    name = models.CharField(max_length=200)
    position = models.CharField(max_length=200, blank=True)
    image_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['position']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.position}"
    
    def get_latest_research(self):
        """Get the most recent research for this politician"""
        return self.research_results.order_by('-created_at').first()


class ResearchResult(models.Model):
    """
    Stores the analysis results for a politician.
    Each result belongs to exactly one politician.
    """
    politician = models.ForeignKey(Politician, on_delete=models.CASCADE, related_name='research_results')
    # position enum
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
        ]
    
    def __str__(self):
        return f"Research on {self.politician.name} ({self.created_at.strftime('%Y-%m-%d')})"
    
    def is_recent(self, days=7):
        """Check if this research is recent (within the specified number of days)"""
        return (timezone.now() - self.created_at).days <= days

class Chat(models.Model):
    """
    Stores a conversation between a user and the assistant.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chats')
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', '-updated_at']),
        ]
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.title} - {self.user.username}"

class Message(models.Model):
    """
    Stores individual messages within a chat.
    """
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
    ]

    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    content = models.TextField()
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['chat', 'timestamp']),
        ]
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.role} message in {self.chat.title} ({self.timestamp.strftime('%Y-%m-%d %H:%M')})"