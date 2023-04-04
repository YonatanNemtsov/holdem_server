from django.urls import path
from . import views

urlpatterns = [
    path("game/<str:table_id>/", views.game, name="game_table"),
]