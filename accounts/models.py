from django.db import models

# We're using Django's built-in User model, so we don't need to define any additional models.

from django.contrib.auth.models import User
from research.models import Politician

class PoliticianPicks(models.Model):
    """
    Stores politician picks for each user.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='politician_picks')
    politicians = models.ManyToManyField(Politician, related_name='picked_by_users')
    
    class Meta:
        verbose_name_plural = "Politician picks"
        
    def __str__(self):
        return f"{self.user.username}'s politician picks"