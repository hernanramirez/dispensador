from django.urls import re_path
from apps.core import consumers

websocket_urlpatterns = [
    re_path(r'ws/alerts/$', consumers.RobotAlertsConsumer.as_asgi()),
]
