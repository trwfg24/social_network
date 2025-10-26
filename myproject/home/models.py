from typing import Any

from django import forms
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models
from pymysql import IntegrityError


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Người dùng phải có email")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser phải có is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser phải có is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(null=True, blank=True)
    # Bỏ username, dùng email làm đăng nhập
    username = None  # bỏ field username mặc định
    email = models.EmailField(unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []  # Không cần thêm trường bắt buộc nào ngoài email

    full_name = models.CharField(max_length=100)
    bio = models.TextField(blank=True, null=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(
        max_length=10,
        choices=[("male", "Nam"), ("female", "Nữ"), ("other", "Khác")],
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    # gắn custom manager
    objects: Any = CustomUserManager()

    def get_friends(self):
        friendships = Friendship.objects.filter(
            models.Q(user1=self)
            | models.Q(
                user2=self
            ),  # SELECT * FROM friendship WHERE (user1_id = self.id OR user2_id = self.id) AND status = 'accepted';
            status="accepted",
        )
        friends = []
        for f in friendships:
            if f.user1 == self:
                friends.append(f.user2)
            else:
                friends.append(f.user1)
        return friends

    def get_friends_count(self):
        return len(self.get_friends())

    def send_friend_request(self, other_user):
        """
        Gửi lời mời kết bạn tới other_user.
        Trả về True nếu gửi thành công, False nếu đã tồn tại hoặc lỗi.
        """
        # Kiểm tra nếu đã có mối quan hệ tồn tại (pending hoặc accepted)
        existing = Friendship.objects.filter(
            models.Q(user1=self, user2=other_user)
            | models.Q(user1=other_user, user2=self)
        ).first()

        if existing:
            # Đã có request hoặc đã là bạn → không tạo mới
            return False

        try:
            Friendship.objects.create(user1=self, user2=other_user, status="pending")
            return True
        except IntegrityError:
            return False


class Conversation(models.Model):
    user1 = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="conversations_started"
    )
    user2 = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="conversations_received"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user1", "user2")  # 1 cặp user chỉ có 1 cuộc trò chuyện

    def get_other_user(self, user):
        """Lấy ra user còn lại trong cuộc trò chuyện"""
        return self.user2 if self.user1 == user else self.user1


class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation, related_name="messages", on_delete=models.CASCADE
    )
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]


class Posts(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    content = models.TextField(blank=True, null=True)
    media = models.ImageField(upload_to="posts/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    likeCount = models.IntegerField(default=0)
    commentCount = models.IntegerField(default=0)


class PostLike(models.Model):
    post = models.ForeignKey(Posts, on_delete=models.CASCADE, related_name="likes")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("post", "user")  # 1 người chỉ like 1 lần


class PostComment(models.Model):
    post = models.ForeignKey(
        "Posts", on_delete=models.CASCADE, related_name="comments"
    )  # Comment thuộc bài viết nào
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="comments"
    )  # Ai comment
    content = models.TextField(blank=True, null=True)  # Nội dung
    image = models.ImageField(
        upload_to="comments/", blank=True, null=True
    )  # Ảnh đính kèm
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="replies"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    likeCount = models.IntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]  # Comment mới lên trước


class CommentLike(models.Model):
    comment = models.ForeignKey(
        PostComment, on_delete=models.CASCADE, related_name="likes"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="comment_likes"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("comment", "user")  # đảm bảo 1 user chỉ like 1 lần


class PostForm(forms.ModelForm):
    class Meta:
        model = Posts
        fields = ["content", "media"]


class ProfileEditForm(forms.ModelForm):
    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={
                "type": "date",  # HTML5 date picker (calendar)
                "class": "form-control",
            }
        ),
    )

    gender = forms.ChoiceField(
        choices=[
            ("", "Chọn giới tính"),
            ("male", "Nam"),
            ("female", "Nữ"),
            ("other", "Khác"),
        ],
        required=False,
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    class Meta:
        model = User
        fields = ["full_name", "bio", "date_of_birth", "avatar", "gender"]
        widgets = {
            "full_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Họ và tên"}
            ),
            "bio": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Giới thiệu về bạn",
                }
            ),
            "avatar": forms.ClearableFileInput(attrs={"class": "form-control-file"}),
        }


class Friendship(models.Model):
    user1 = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="friendships_initiated"
    )
    user2 = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="friendships_received"
    )
    created_at = models.DateTimeField(auto_now_add=True)  # Ngày trở thành bạn
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Chờ xác nhận"),
            ("accepted", "Đã chấp nhận"),
        ],
        default="pending",
    )

    class Meta:
        unique_together = ("user1", "user2")  # Tránh trùng cặp bạn bè

    # def save(self, *args, **kwargs):
    #     # Đảm bảo luôn lưu theo thứ tự ID tăng dần
    #     if self.user1_id > self.user2_id:
    #         self.user1, self.user2 = self.user2, self.user1
    #     super().save(*args, **kwargs)
