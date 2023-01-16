
from random import randint
import json

from asgiref.sync import async_to_sync
from channels.auth import login
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async

from .models import GameLog, GameTable




class GameConsumer(AsyncJsonWebsocketConsumer):
    pass
