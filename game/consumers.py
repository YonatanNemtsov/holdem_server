
from random import randint
from channels.auth import login
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from .models import GameLog, GameTable




class GameConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        pass
    