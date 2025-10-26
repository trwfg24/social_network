from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from home.models import Conversation, Message
from realtime.models import Notification


def notifications(request):
    if request.user.is_authenticated:
        notifications = Notification.objects.filter(user=request.user).order_by(
            "-created_at"
        )
        unread_count = notifications.filter(is_read=False).count()

        # Đếm tin nhắn chưa đọc
        unread_messages = (
            Message.objects.filter(
                conversation__in=Conversation.objects.filter(
                    Q(user1=request.user) | Q(user2=request.user)
                ),
                is_read=False,
            )
            .exclude(sender=request.user)
            .count()
        )
    else:
        notifications = []
        unread_count = 0
        unread_messages = 0
    return {
        "notifications": notifications,
        "unread_count": unread_count,
        "unread_messages_count": unread_messages,
    }
