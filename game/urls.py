from django.urls import path
from . import views

urlpatterns = [
    path('game/', views.game,name='game'),
    path('',views.login,name='login')
]