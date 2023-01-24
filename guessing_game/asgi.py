"""
ASGI config for guessing_game project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

from channels.routing import ProtocolTypeRouter, URLRouter, ChannelNameRouter
from channels.auth import AuthMiddlewareStack
from game import consumers

from game.routing import ws_urlpatterns
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'minimal_rt_site.settings')

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket' : AuthMiddlewareStack(URLRouter(ws_urlpatterns)),
    'channel' : ChannelNameRouter(
        {
            'test':consumers.Test.as_asgi(),
            
        }

    )
})