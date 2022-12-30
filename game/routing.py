from django.urls import path

from . import consumers
ws_urlpatterns = [
    path('ws/some_url/', consumers.WSConsumer.as_asgi())
]