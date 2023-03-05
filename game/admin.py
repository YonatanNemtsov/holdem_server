from django.contrib import admin
from .models import GameTable, UserAccount, Player
# Register your models here.
admin.site.register(GameTable)
admin.site.register(UserAccount)
admin.site.register(Player)