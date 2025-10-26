from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db import models
from django.db.models import Q
from django.http import Http404, JsonResponse

# Create your views here.
# myapp/views.py
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from home.models import CommentLike, Conversation, PostComment, PostLike, Posts, User

from .models import Notification
from .utils import get_user_status, send_notification


@login_required
def like_post(request, post_id):
    post = get_object_or_404(Posts, id=post_id)

    # Kiểm tra đã like chưa
    existing_like = PostLike.objects.filter(post=post, user=request.user).first()

    if existing_like:
        # Nếu đã like → unlike
        existing_like.delete()
        post.likeCount = PostLike.objects.filter(post=post).count()
        post.save(update_fields=["likeCount"])
        return JsonResponse({"status": "unliked", "likeCount": post.likeCount})
    else:
        # Nếu chưa like → like
        PostLike.objects.create(post=post, user=request.user)
        post.likeCount = PostLike.objects.filter(post=post).count()
        post.save(update_fields=["likeCount"])

        # Chỉ gửi noti nếu người like KHÔNG phải là chủ bài viết
        if post.user != request.user:
            send_notification(
                user=post.user,
                message=f"❤️ {request.user.full_name} đã thích bài viết của bạn",
                post=post,
                sender=request.user,
            )

        return JsonResponse({"status": "liked", "likeCount": post.likeCount})


@login_required
def add_comment(request, post_id):
    try:
        post = Posts.objects.get(id=post_id)
    except Posts.DoesNotExist:
        return JsonResponse({"error": "Post not found"}, status=404)

    content = request.POST.get("content", "").strip()
    parent_id = request.POST.get("parent_id")  # Nếu là reply
    image = request.FILES.get("image")  # file ảnh

    parent = None
    if parent_id:
        try:
            parent = PostComment.objects.get(id=parent_id, post=post)
        except PostComment.DoesNotExist:
            return JsonResponse({"error": "Parent comment not found"}, status=404)

    # Tạo comment mới
    comment = PostComment.objects.create(
        post=post,
        user=request.user,
        content=content,
        image=image if image else None,
        parent=parent,
    )

    # Tăng commentCount của post
    post.commentCount = (post.commentCount or 0) + 1
    post.save(update_fields=["commentCount"])

    # Gửi noti cho chủ bài viết (nếu không phải tự comment)
    if post.user != request.user:
        send_notification(
            user=post.user,
            message=f"💬 {request.user.full_name} đã bình luận bài viết của bạn",
            post=post,
            comment=comment,
            sender=request.user,
        )

    # render partial template
    html = render_to_string("base/comment_item.html", {"c": comment}, request=request)

    return JsonResponse(
        {"success": True, "html": html, "commentCount": post.commentCount}
    )


@login_required(login_url="login")
def add_friend(request, user_id):
    other_user = get_object_or_404(User, pk=user_id)

    success = request.user.send_friend_request(other_user)

    # Redirect về lại trang gốc
    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER", "/")

    if success:
        # Gọi hàm tiện ích gửi notification
        send_notification(
            user=other_user,
            sender=request.user,
            message=f"👥 {request.user.full_name} đã gửi cho bạn lời mời kết bạn.",
            post=None,
            comment=None,
        )
    return redirect(next_url)


@login_required
def mark_notification_read(request):
    notification_id = request.GET.get("id")
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()
        return JsonResponse({"status": "ok"})
    except Notification.DoesNotExist:
        return JsonResponse({"status": "error"})


@login_required
def chat_page(request):
    user = request.user
    conversations = Conversation.objects.filter(
        Q(user1=user) | Q(user2=user)
    ).prefetch_related("messages")

    conv_data = []
    for conv in conversations:
        other = conv.user2 if conv.user1 == user else conv.user1
        conv_data.append(
            {
                "conversation": conv,
                "other_user": other,
                "status": get_user_status(other),
            }
        )

    return render(
        request,
        "chat/chat.html",
        {
            "conversations": conv_data,
            "current_user_name": request.user.full_name,
            "current_user_id": user.id,
        },
    )


@login_required
def get_messages(request, conv_id):
    try:
        conv = Conversation.objects.get(id=conv_id)
    except Conversation.DoesNotExist:
        raise Http404("Conversation không tồn tại")

    # check user có thuộc cuộc trò chuyện không
    if request.user not in [conv.user1, conv.user2]:
        return JsonResponse({"error": "Không có quyền xem"}, status=403)

    # Đánh dấu tất cả tin nhắn trong conversation này là đã đọc (trừ tin nhắn của chính mình)
    conv.messages.exclude(sender=request.user).update(is_read=True)  # type: ignore

    messages = conv.messages.select_related("sender")  # type: ignore

    data = [
        {
            "id": m.id,
            "sender_id": m.sender_id,
            "sender_name": m.sender.full_name,  # để hiện avatar/chữ cái
            "text": m.text,
            "time": m.created_at.strftime("%H:%M"),
            "is_self": m.sender_id == request.user.id,
            "sender_avatar": m.sender.avatar.url if m.sender.avatar else None,
        }
        for m in messages
    ]
    return JsonResponse(data, safe=False)


@login_required
def get_status(request, user_id):
    User = get_user_model()
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({"status": "Không tìm thấy"}, status=404)

    return JsonResponse({"status": get_user_status(user)})  # <-- Gọi hàm ở đây


@login_required
def search_users(request):
    q = request.GET.get("q", "").strip()
    if not q:
        return JsonResponse([], safe=False)

    users = User.objects.filter(full_name__icontains=q).exclude(id=request.user.id)[:10]
    data = []
    for u in users:
        data.append(
            {
                "id": u.id,
                "name": u.full_name,
                "avatar": u.avatar.url if getattr(u, "avatar", None) else None,
            }
        )
    return JsonResponse(data, safe=False)


@login_required
def get_or_create_conversation(request, user_id):
    try:
        other = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)

    # Tìm conversation giữa 2 user (user1-user2 hoặc user2-user1)
    conv = Conversation.objects.filter(
        (Q(user1=request.user) & Q(user2=other))
        | (Q(user1=other) & Q(user2=request.user))
    ).first()

    # Nếu chưa có thì tạo mới
    if not conv:
        conv = Conversation.objects.create(user1=request.user, user2=other)

    return JsonResponse({"id": conv.id})  # type: ignore


@login_required
def get_unread_messages_count(request):
    """API để lấy số lượng tin nhắn chưa đọc"""
    from home.models import Message

    unread_count = (
        Message.objects.filter(
            conversation__in=Conversation.objects.filter(
                Q(user1=request.user) | Q(user2=request.user)
            ),
            is_read=False,
        )
        .exclude(sender=request.user)
        .count()
    )

    return JsonResponse({"unread_count": unread_count})


@login_required
def like_comment(request, comment_id):
    """API để like/unlike comment"""
    try:
        comment = PostComment.objects.get(id=comment_id)
    except PostComment.DoesNotExist:
        return JsonResponse({"error": "Comment not found"}, status=404)

    # Kiểm tra đã like chưa
    existing_like = CommentLike.objects.filter(
        comment=comment, user=request.user
    ).first()

    if existing_like:
        # Nếu đã like → unlike
        existing_like.delete()
        comment.likeCount = max(0, comment.likeCount - 1)
        comment.save(update_fields=["likeCount"])
        return JsonResponse({"status": "unliked", "likeCount": comment.likeCount})
    else:
        # Nếu chưa like → like
        CommentLike.objects.create(comment=comment, user=request.user)
        comment.likeCount = (comment.likeCount or 0) + 1
        comment.save(update_fields=["likeCount"])

        # Gửi thông báo cho chủ comment (nếu không phải tự like)
        if comment.user != request.user:
            send_notification(
                user=comment.user,
                message=f"❤️ {request.user.full_name} đã thích bình luận của bạn",
                post=comment.post,
                comment=comment,
                sender=request.user,
            )

        return JsonResponse({"status": "liked", "likeCount": comment.likeCount})


@login_required
def reply_comment(request, comment_id):
    """API để trả lời comment"""
    try:
        parent_comment = PostComment.objects.get(id=comment_id)
    except PostComment.DoesNotExist:
        return JsonResponse({"error": "Comment not found"}, status=404)

    content = request.POST.get("content", "").strip()
    image = request.FILES.get("image")

    if not content and not image:
        return JsonResponse({"error": "Content or image required"}, status=400)

    # Tạo reply
    reply = PostComment.objects.create(
        post=parent_comment.post,
        user=request.user,
        content=content,
        image=image if image else None,
        parent=parent_comment,
    )

    # Tăng commentCount của post
    post = parent_comment.post
    post.commentCount = (post.commentCount or 0) + 1
    post.save(update_fields=["commentCount"])

    # Gửi thông báo cho chủ comment được reply (nếu không phải tự reply)
    if parent_comment.user != request.user:
        send_notification(
            user=parent_comment.user,
            message=f"💬 {request.user.full_name} đã trả lời bình luận của bạn",
            post=parent_comment.post,
            comment=reply,
            sender=request.user,
        )

    # Render partial template
    html = render_to_string("base/comment_item.html", {"c": reply}, request=request)

    return JsonResponse(
        {
            "success": True,
            "html": html,
            "commentCount": post.commentCount,
            "comment_id": reply.id,  # type: ignore
        }
    )
