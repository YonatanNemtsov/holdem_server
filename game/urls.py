from django.urls import path
from . import views

urlpatterns = [
    path("game/<str:table_name>/", views.game, name="game_table"),
    path("game/<str:table_name>/<int:sit_number>/", views.sit, name='sit'),

]