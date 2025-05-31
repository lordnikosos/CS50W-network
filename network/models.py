from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    pass

class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def formatted_timestamp(self):
        return self.timestamp.strftime("%d %b %Y at %H:%M:%S")
        
    def time_since(self):
        return str(timezone.now() - self.timestamp).split('.')[0]

    def __str__(self):
        return f"{self.user.username} posted at {self.formatted_timestamp()}  | {self.time_since()} minutes ago"


