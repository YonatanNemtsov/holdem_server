from random import shuffle, randint
import asyncio
import websockets.client
import json
from dataclasses import dataclass, field

from channels.generic.websocket import AsyncJsonWebsocketConsumer, AsyncConsumer
from channels.db import database_sync_to_async
from asgiref.sync import async_to_sync
from django.contrib.auth.models import User

from .models import GameTable, UserAccount

class GameConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        """ Connecting to a poker table websocket. """

        self.table_id = int(self.scope['url_route']['kwargs']['table_id'])
        self.user = self.scope['user']
        print(self.user.id, self.user.username, self.user)
        try:
            table = await self.get_db_table_by_id(self.table_id)
            self.table_config = table.config.copy()
        except:
            await self.close()
            return
        print(self.table_config)
        await self.connect_to_table()
        asyncio.create_task(self.beggin_recv())
        await self.accept()
        return
    
    #TODO: write the function.
    async def connect_to_table(self):
        self.table_connection: websockets.client.ClientConnection = await websockets.client.connect("ws://localhost:8765/table")
        await self.table_connection.send(json.dumps({'type':'connection_request','data': {'user_id':self.user.id}}))
        
    async def beggin_recv(self):
        """ Recieving updates and responses from table server """
        while True:
            message = await self.table_connection.recv()
            await self.recieve_table_message(message)
    
    async def add_table_request(self):
        await self.send_to_table_server()
    
    async def recieve_table_message(self, message):
        """recieve updates and responses from the table server"""
        TABLE_MESSAGE_TYPES = ['table_view_update', 'sit_response', 'move_response']
        if type(message) == str:
            message = json.loads(message)
        print(message)
        if message['type'] == 'table_view_update':
            await self.send_json(message)
    
    async def send_to_table_server(self, consumer_request: dict):
        CONSUMER_MESSAGE_TYPES = ['sit_request', 'move_request', 'add_chips_request', 'init_table_request']
        if type(consumer_request) == dict:
            consumer_request = json.dumps(consumer_request)

        await self.table_connection.send(consumer_request)
    

    #TODO: implement sub functions. 
    async def _recieve_sit_request(self, client_request):
        pass

    async def _recieve_move_request(self, client_request):
        pass
    
    async def _recieve_add_chips_request(self, client_request):
        pass
    

    async def receive_json(self, client_request, **kwargs):
        """ Recieving messages from the client """
        CLIENT_MESSAGE_TYPES = ['sit_request', 'move_request', 'add_chips_request']
        consumer_request = client_request.copy()
        
        consumer_request['data'].update({'user_id': self.user.id, 'table_id': self.table_id})
        
        if consumer_request['type'] == 'sit_request':
            await self.send_to_table_server(consumer_request)
        
        if consumer_request['type'] == 'move_request':
            print(consumer_request)
            await self.send_to_table_server(consumer_request)
        
    async def disconnect(self, code):
        await self.table_connection.close()
        return await self.close()
    
    @database_sync_to_async
    def get_db_table_by_id(self, table_id: str) -> GameTable:
        return GameTable.objects.get(id=table_id)
    
class ChipBalanceUpdateWorker(AsyncConsumer):
    pass