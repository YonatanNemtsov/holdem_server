from random import shuffle, randint
import asyncio
import websockets.client
import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer, AsyncConsumer, JsonWebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import async_to_sync
from django.contrib.auth.models import User

from holdem_core.core_game.holdem_table import HoldemTable,HoldemTableConfig,HoldemTablePlayer

from .models import GameTable, UserAccount

class GameWatcherConsumer(AsyncJsonWebsocketConsumer):
    pass


class TableWebsocketClient:
    pass

class DatabaseUpdateManagerConsumerd(JsonWebsocketConsumer):
    pass

class GameConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        """ Connecting to a poker table websocket. """

        self.table_id = self.scope['url_route']['kwargs']['table_id']
        print(self.scope['user'].id, self.scope['user'].username, self.scope['user'])
        try:
            await self.get_db_table_by_id(self.table_id)
        except:
            await self.close()
            return
        await self.connect_to_table()
        asyncio.create_task(self.beggin_recv())
        print(self.table_connection)
        await self.table_connection.send('hello')
        await self.accept()
        return
    
    async def connect_to_table(self):
        self.table_connection: websockets.client.ClientConnection = await websockets.client.connect("ws://localhost:8765/table")
        
    async def beggin_recv(self):
        while True:
            message = await self.table_connection.recv()
            print(message)

    async def table_response_handler(self, response):
        pass

    async def send_to_table_server(self, message):
        if type(message) == dict:
            message = json.dumps(message)

        await self.table_connection.send(message)
    
    async def receive_json(self, content, **kwargs):
        """ Recieving messages from the client """
        MESSAGE_TYPES = ['sit_request', 'move_request', 'add_chips_request']
        await self.send_to_table_server(content)
    
    async def disconnect(self, code):
        await self.table_connection.close()
    
        return await self.close()
    
    @database_sync_to_async
    def get_db_table_by_id(self, table_id: str):
        return GameTable.objects.get(id=table_id)