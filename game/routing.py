from django.urls import path,re_path

from . import consumers
ws_urlpatterns = [
    #path('ws/some_url/', consumers.WSConsumer.as_asgi())
    re_path(r"ws/game/(?P<table_id>\w+)/$", consumers.GameConsumer.as_asgi()),
]