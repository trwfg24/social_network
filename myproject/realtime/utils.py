# myapp/utils.py
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone


def send_notification(user, message, sender=None, post=None, comment=None):
    from .models import Notification

    # Tạo noti
    notification = Notification.objects.create(
        user=user, message=message, sender=sender, post=post, comment=comment
    )

    layer = get_channel_layer()
    async_to_sync(layer.group_send)(  # type: ignore
        f"user_{user.id}",
        {
            "type": "send_notification",
            "id": notification.id,  # type: ignore
            "message": message,
            "post_id": notification.post.id if notification.post else None,  # type: ignore
            "count": Notification.objects.filter(user=user, is_read=False).count(),
            "comment_id": notification.comment.id if notification.comment else None,  # type: ignore
            "sender_id": notification.sender.id if notification.sender else None,  # type: ignore
            "sender_img_url": notification.sender.avatar.url if notification.sender and notification.sender.avatar else None,  # type: ignore
            "sender_name": notification.sender.full_name if notification.sender and notification.sender.full_name else None,  # type: ignore
        },
    )


def get_user_status(user):
    """Trả về chuỗi trạng thái của user"""
    if getattr(user, "is_online", False):
        return "🟢 Đang hoạt động"

    if not getattr(user, "last_seen", None):
        return "Chưa từng hoạt động"

    delta = timezone.now() - user.last_seen
    minutes = int(delta.total_seconds() // 60)
    hours = int(delta.total_seconds() // 3600)
    days = delta.days

    if minutes < 1:
        return "Vừa mới hoạt động"
    elif minutes < 60:
        return f"Hoạt động {minutes} phút trước"
    elif hours < 24:
        return f"Hoạt động {hours} giờ trước"
    else:
        return f"Hoạt động {days} ngày trước"
