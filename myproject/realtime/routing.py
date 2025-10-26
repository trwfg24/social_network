from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import re_path
from realtime.consumers import ChatConsumer, NotificationConsumer

websocket_urlpatterns = [
    re_path(r"ws/notifications/$", NotificationConsumer.as_asgi()),  # type: ignore
    re_path(r"ws/chat/(?P<conv_id>\d+)/$", ChatConsumer.as_asgi()),  # type: ignore
]

application = ProtocolTypeRouter(
    {
        "websocket": AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
    }
)
