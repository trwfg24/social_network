import random

from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string

from .models import (
    Conversation,
    Friendship,
    Message,
    PostComment,
    PostForm,
    PostLike,
    Posts,
    ProfileEditForm,
    User,
)


def suggest_friends(current_user, limit=10):
    # Lấy danh sách bạn bè của current_user
    my_friendships = Friendship.objects.filter(
        Q(user1=current_user) | Q(user2=current_user), status="accepted"
    )
    my_friends = set(
        f.user1 if f.user2 == current_user else f.user2 for f in my_friendships
    )

    # Lấy tất cả user khác
    all_users = User.objects.exclude(id=current_user.id)

    suggestions = []

    for u in all_users:
        # Bỏ qua nếu đã là bạn
        if u in my_friends:
            continue

        # Kiểm tra có pending request không
        pending = Friendship.objects.filter(
            (Q(user1=current_user, user2=u) | Q(user1=u, user2=current_user)),
            status="pending",
        ).exists()
        if pending:
            continue

        # Tính số bạn chung
        u_friendships = Friendship.objects.filter(
            Q(user1=u) | Q(user2=u), status="accepted"
        )
        u_friends = set(f.user1 if f.user2 == u else f.user2 for f in u_friendships)

        mutual_count = len(my_friends.intersection(u_friends))

        if mutual_count > 0:
            suggestions.append((u, mutual_count))

    # Sắp xếp theo mutual_count giảm dần
    suggestions.sort(key=lambda x: x[1], reverse=True)

    # Trả về giới hạn limit
    return suggestions[:limit]


# Create your views here.
def logout_view(request):
    if request.user.is_authenticated:
        request.user.is_online = False
        request.user.save()
    logout(request)
    return redirect("login")


def login(request):
    if request.method == "POST":
        form_type = request.POST.get("form_type")

        if form_type == "sign_up":
            name = request.POST.get("fullname")
            email = request.POST.get("email")
            password = request.POST.get("password")

            if User.objects.filter(email=email).exists():
                messages.error(request, "Email đã được đăng ký!")
                return render(request, "login/login.html")

            User.objects.create_user(email=email, full_name=name, password=password)
            messages.success(request, "Đăng ký thành công! Vui lòng đăng nhập.")
            return redirect("login")

        elif form_type == "sign_in":
            email = request.POST.get("email")
            password = request.POST.get("password")

            from django.contrib.auth import authenticate
            from django.contrib.auth import login as auth_login

            user = authenticate(request, email=email, password=password)
            if user is not None:
                auth_login(request, user)
                return redirect("home")
            else:
                messages.error(request, "Email hoặc mật khẩu không đúng!")

    return render(request, "login/login.html")


@login_required(login_url="login")
def home(request):
    posts = list(Posts.objects.all())
    random.shuffle(posts)
    posts = posts[:100]

    liked_posts = set(
        PostLike.objects.filter(user=request.user).values_list("post_id", flat=True)
    )

    friendships = Friendship.objects.filter(status="accepted").filter(
        Q(user1=request.user) | Q(user2=request.user)
    )

    friends = []
    for f in friendships:
        friend = f.user2 if f.user1 == request.user else f.user1
        friends.append(
            {
                "name": friend.full_name,
                "avatar": friend.avatar.url if friend.avatar else None,
                "id": friend.id,  # type: ignore
            }
        )

    numberFriend = len(friends)
    countPost = Posts.objects.filter(user=request.user).count()
    totalLikes = PostLike.objects.filter(post__user=request.user).count()
    results = suggest_friends(request.user, limit=10)

    context = {
        "user": request.user,
        "posts": posts,
        "user_liked_posts": liked_posts,
        "friends": friends,
        "numberfriends": numberFriend,
        "numberposts": countPost,
        "totallikeposts": totalLikes,
        "suggestfriend": results,
    }

    return render(request, "home/home.html", context)


@login_required(login_url="login")
def create_post(request):
    form = PostForm(request.POST, request.FILES)
    if form.is_valid():
        post = form.save(commit=False)
        post.user = request.user
        post.save()
        messages.success(request, "Đăng bài thành công!")  # thêm dòng này
    return redirect("home")


@login_required(login_url="login")
def profile_view(request, user_id=None):
    if user_id:
        profile_user = get_object_or_404(User, id=user_id)
    else:
        profile_user = get_object_or_404(User, id=request.user.id)

    posts = Posts.objects.filter(user=profile_user).order_by("-created_at")

    form = ProfileEditForm(instance=request.user)

    relationship = Friendship.objects.filter(
        Q(user1=request.user, user2=profile_user)
        | Q(user1=profile_user, user2=request.user)
    ).first()
    friendship_status = None
    if relationship:
        friendship_status = relationship.status  # 'pending' hoặc 'accepted'
        friendship_sender_id = relationship.user1.id  # type: ignore
    else:
        friendship_status = None
        friendship_sender_id = None

    friendships = Friendship.objects.filter(status="accepted").filter(
        Q(user1=profile_user) | Q(user2=profile_user)
    )

    friends = []
    for f in friendships:
        friend = f.user2 if f.user1 == profile_user else f.user1
        friends.append(
            {
                "name": friend.full_name,
                "avatar": friend.avatar.url if friend.avatar else None,
                "id": friend.id,  # type: ignore
            }
        )

    liked_posts = set(
        PostLike.objects.filter(user=request.user).values_list("post_id", flat=True)
    )

    highlight_post_id = request.GET.get("highlight")
    highlight_comment_id = request.GET.get("comment")

    context = {
        "profile_user": profile_user,
        "current_user": request.user,
        "posts": posts,
        "user_liked_posts": liked_posts,
        "form": form,
        "friendship_status": friendship_status,
        "friendship_sender_id": friendship_sender_id,
        "friends": friends,
        "highlight_post_id": highlight_post_id,
        "highlight_comment_id": highlight_comment_id,
    }
    return render(request, "personal/personal.html", context)


@login_required(login_url="login")
def edit_profile(request):
    form = ProfileEditForm(request.POST, request.FILES, instance=request.user)
    if form.is_valid():
        form.save()
        # Có thể thêm messages nếu muốn
    else:
        # Xử lý lỗi nếu cần, hoặc bỏ qua
        pass
    return redirect("personal")


@login_required(login_url="login")
def accept_request(request, user_id):
    other_user = get_object_or_404(User, pk=user_id)

    # Chỉ xử lý khi có lời mời kết bạn từ other_user → request.user
    friendship = Friendship.objects.filter(
        user1=other_user, user2=request.user, status="pending"
    ).first()

    if friendship:
        friendship.status = "accepted"
        friendship.save()

    # Ưu tiên redirect về "next" trong form, fallback về referer
    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER", "/")

    # Sắp xếp user theo id để tránh trùng lặp (A-B và B-A)
    if request.user.id < other_user.id:  # type: ignore
        user1, user2 = request.user, other_user
    else:
        user1, user2 = other_user, request.user
    conv, created = Conversation.objects.get_or_create(user1=user1, user2=user2)
    if created:
        Message.objects.create(
            conversation=conv,
            sender=request.user,
        )
    return redirect(next_url)


@login_required(login_url="login")
def cancel_request(request, user_id):
    other_user = get_object_or_404(User, pk=user_id)
    Friendship.objects.filter(
        Q(user1=request.user, user2=other_user, status="pending")
        | Q(user1=other_user, user2=request.user, status="pending")
    ).delete()

    # Redirect về trang gốc (nếu có) hoặc về referer
    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER", "/")
    return redirect(next_url)


@login_required(login_url="login")
def delete_friend(request, user_id):
    other_user = get_object_or_404(User, pk=user_id)
    Friendship.objects.filter(
        Q(user1=request.user, user2=other_user, status="accepted")
        | Q(user1=other_user, user2=request.user, status="accepted")
    ).delete()
    # Redirect về trang gốc (nếu có) hoặc về referer
    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER", "/")
    return redirect(next_url)


def friends_list_view(request):
    # Lấy các friendship đã được chấp nhận
    friendships = Friendship.objects.filter(status="accepted").filter(
        (Q(user1=request.user) | Q(user2=request.user))
    )

    friends = []
    for f in friendships:
        # Nếu user hiện tại là user1 thì bạn là user2, ngược lại thì bạn là user1
        friend = f.user2 if f.user1 == request.user else f.user1
        full_name = friend.get_full_name() or friend.username
        friends.append(
            {
                "name": full_name,
                "initials": "".join([p[0].upper() for p in full_name.split()]) if full_name else "",  # type: ignore
            }
        )

    return render(request, "friends_modal.html", {"friends": friends})


@login_required(login_url="login")
def delete_post(request, post_id):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Phương thức không hợp lệ"})

    try:
        post = Posts.objects.get(id=post_id)
    except Posts.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Bài viết không tồn tại"})

    # Chỉ cho user chủ bài xóa
    if post.user != request.user:
        return JsonResponse(
            {"status": "error", "message": "Bạn không có quyền xóa bài viết này"}
        )

    post.delete()
    return JsonResponse({"status": "ok"})


def get_comments(request, post_id):
    # Chỉ lấy comment gốc (không có parent), replies sẽ được lấy qua c.replies.all trong template
    comments = (
        PostComment.objects.filter(post_id=post_id, parent__isnull=True)
        .select_related("user")
        .prefetch_related("replies__user")  # Tối ưu query cho replies
        .order_by("-created_at")
    )
    return render(
        request,
        "base/comments_list.html",
        {"comments": comments, "current_user": request.user},
    )


@login_required
def delete_comment(request, comment_id):
    try:
        comment = PostComment.objects.get(id=comment_id)
    except PostComment.DoesNotExist:
        return JsonResponse({"error": "Comment not found"}, status=404)

    # Chỉ cho phép chủ comment hoặc chủ bài viết xoá
    if request.user != comment.user and request.user != comment.post.user:
        return JsonResponse({"error": "Permission denied"}, status=403)

    post = comment.post

    # Xoá comment
    comment.delete()

    # Trừ commentCount
    if post.commentCount > 0:
        post.commentCount -= 1
        post.save(update_fields=["commentCount"])

    return JsonResponse(
        {
            "success": True,
            "post_id": post.id,
            "comment_id": comment_id,
            "commentCount": post.commentCount,
        }
    )


# @login_required
# def findfriend(request):
#     keyword = request.GET.get("q", "")
#     user = request.user

#     # lấy danh sách bạn bè hiện tại ngay từ đầu
#     my_friends = set(f.id for f in user.get_friends())

#     results = []
#     if keyword:
#         # tìm user theo tên (loại bỏ chính mình + loại bỏ bạn bè đã có)
#         users = User.objects.filter(
#             Q(full_name__icontains=keyword)
#         ).exclude(id__in=my_friends | {user.id})

#         # tính số bạn chung
#         for u in users:
#             u_friends = set(f.id for f in u.get_friends())
#             mutual_count = len(my_friends & u_friends)
#             results.append((u, mutual_count))

#         # sắp xếp giảm dần theo mutual_count
#         results.sort(key=lambda x: x[1], reverse=True)

#     return render(request, "findfriend/findfriend.html", {"results": results, "keyword": keyword})


# @login_required
# def findfriend(request):
#     keyword = request.GET.get("q", "")
#     user = request.user

#     results = []
#     if keyword:
#         # tìm user theo tên (loại bỏ chính mình)
#         users = User.objects.filter(
#             Q(full_name__icontains=keyword)
#         ).exclude(id=user.id)

#         # danh sách bạn của current user
#         my_friends = set([f.id for f in user.get_friends()])   # <-- sửa ở đây

#         # tính số bạn chung
#         for u in users:
#             u_friends = set([f.id for f in u.get_friends()])   # <-- sửa ở đây
#             mutual_count = len(my_friends & u_friends)
#             results.append((u, mutual_count))

#         # sắp xếp giảm dần theo mutual_count
#         results.sort(key=lambda x: x[1], reverse=True)

#     return render(request, "findfriend/findfriend.html", {"results": results, "keyword": keyword})


@login_required(login_url="login")
def findfriend(request):
    keyword = request.GET.get("q", "")
    current_user = request.user

    results = []
    if keyword:
        # tìm user theo tên, bỏ bản thân
        users = User.objects.filter(Q(full_name__icontains=keyword)).exclude(
            id=current_user.id
        )

        # danh sách bạn của current_user
        my_friendships = Friendship.objects.filter(status="accepted").filter(
            Q(user1=current_user) | Q(user2=current_user)
        )

        my_friends = set(
            f.user2 if f.user1 == current_user else f.user1 for f in my_friendships
        )

        for u in users:
            # tính bạn chung
            u_friendships = Friendship.objects.filter(status="accepted").filter(
                Q(user1=u) | Q(user2=u)
            )

            u_friends = set(f.user2 if f.user1 == u else f.user1 for f in u_friendships)

            mutual_count = len(my_friends & u_friends)

            # quan hệ giữa current_user và u
            relationship = Friendship.objects.filter(
                Q(user1=current_user, user2=u) | Q(user1=u, user2=current_user)
            ).first()

            if relationship:
                friendship_status = relationship.status  # 'pending' hoặc 'accepted'
                friendship_sender_id = relationship.user1.id  # type: ignore
            else:
                friendship_status = None
                friendship_sender_id = None

            results.append((u, mutual_count, friendship_status, friendship_sender_id))

        # sắp xếp theo số bạn chung giảm dần
        results.sort(key=lambda x: x[1], reverse=True)

    return render(
        request,
        "findfriend/findfriend.html",
        {
            "results": results,
            "keyword": keyword,
            "current_user": current_user,
        },
    )


@login_required
def delete_conversation(request, conversation_id):
    """
    Xóa 1 conversation và toàn bộ messages liên quan.
    Chỉ user trong cuộc trò chuyện mới có quyền xoá.
    """
    conversation = get_object_or_404(Conversation, id=conversation_id)

    # Chỉ cho phép user1 hoặc user2 được xóa
    if request.user != conversation.user1 and request.user != conversation.user2:
        return JsonResponse(
            {"success": False, "error": "Bạn không có quyền xoá cuộc trò chuyện này."},
            status=403,
        )

    conversation.delete()  # Nhờ on_delete=CASCADE → xoá hết message liên quan
    return JsonResponse({"success": True, "message": "Đã xoá cuộc trò chuyện."})
