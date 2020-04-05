import os
import django
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "LiveStream.settings")
django.setup()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from LiveStreamApp import routings



application = ProtocolTypeRouter({
    'websocket' : AuthMiddlewareStack(
        URLRouter(
            routings.websocket_urlpatterns
        )
    ),
})

# application = get_default_application()