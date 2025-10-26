from django.db import models
from home.models import User,Posts,PostComment
# Create your models here.

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_notifications')  # người gửi
    message = models.CharField(max_length=255)
    post = models.ForeignKey(Posts, on_delete=models.CASCADE, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    comment = models.ForeignKey(PostComment, on_delete=models.CASCADE, null=True, blank=True)  # liên kết comment
    
    class Meta:
        ordering = ['-created_at']  # mặc định sắp xếp noti mới nhất lên trước