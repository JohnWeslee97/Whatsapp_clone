from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Profile(models.Model):
    user      = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} Profile"

    def get_last_seen_display(self):
        """Centralised display logic — no more scattered strftime calls."""
        if self.is_online:
            return 'Online'
        if self.last_seen:
            return self.last_seen.strftime('Last seen %d %b at %I:%M %p')
        return ' Offline'

class Message(models.Model):
    sender    = models.ForeignKey(User, related_name='sent_messages',     on_delete=models.CASCADE)
    receiver  = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE)
    content   = models.TextField(max_length=2000)  
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read   = models.BooleanField(default=False, db_index=True) 
    class Meta:
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['sender', 'receiver', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.sender} → {self.receiver}: {self.content[:30]}"