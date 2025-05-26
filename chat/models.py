from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from research.models import ResearchResult

class Chat(models.Model):
    """
    Stores chat information.
    Can be associated with a user (authenticated) or be temporary (unauthenticated).
    """
    politician = models.CharField(max_length=200)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    research_report = models.ForeignKey(ResearchResult, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['user', '-created_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        user_str = self.user.username if self.user else "Anonymous"
        return f"Chat about {self.politician} by {user_str} ({self.created_at.strftime('%Y-%m-%d')})"

    @staticmethod
    def remove_old_temporary_chats():
        """
        Removes temporary chats (user=None) that are older than 24 hours.
        This method can be called by a scheduled task or a management command.
        """
        # Calculate the cutoff time (24 hours ago)
        cutoff_time = timezone.now() - timedelta(hours=24)

        # Get all temporary chats older than the cutoff time
        old_chats = Chat.objects.filter(user=None, created_at__lt=cutoff_time)

        # Log the number of chats to be deleted
        count = old_chats.count()
        print(f"Removing {count} temporary chats older than 24 hours")

        # Delete the old chats
        old_chats.delete()

        return count


class QandA(models.Model):
    """
    Stores questions and answers related to a chat.
    """
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='qanda_set')
    question = models.TextField()
    answer = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['chat', '-created_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"Q&A in chat {self.chat.id}: {self.question[:30]}..."
