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
    
    def like_count(self):
        return self.likes.count()
        
    def is_liked_by(self, user):
        if user.is_authenticated:
            return self.likes.filter(user=user).exists()
        return False

class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post')\
        
    def __str__(self):
        return f"{self.user.username} likes {self.post.id}"
    
class Follow(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name="following")
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name="followers")
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('follower', 'following')
    
    def __str__(self):
        return f"{self.follower} follows {self.following}"
