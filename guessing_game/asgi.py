"""
ASGI config for guessing_game project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/howto/deployment/asgi/
"""

import os
import django
from channels.security.websocket import AllowedHostsOriginValidator
from channels.routing import ProtocolTypeRouter, URLRouter, ChannelNameRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'guessing_game.settings')
django_asgi_app = get_asgi_application()

from game.routing import ws_urlpatterns
from game import consumers

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket' : AllowedHostsOriginValidator(AuthMiddlewareStack(URLRouter(ws_urlpatterns))),
    'channel' : ChannelNameRouter(
        {
            'test':consumers.Test.as_asgi(),
            
        }

    )
})