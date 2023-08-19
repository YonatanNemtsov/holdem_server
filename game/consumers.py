import asyncio
import websockets.client
import json

from channels.generic.websocket import AsyncJsonWebsocketConsumer, AsyncConsumer
from channels.db import database_sync_to_async
from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model

from .models import GameTable, UserAccount

User = get_user_model()

class GameConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        """ Connecting to a poker table websocket. """

        self.table_id = int(self.scope['url_route']['kwargs']['table_id'])
        self.user = self.scope['user']
        try:
            table = await self.get_db_table_by_id(self.table_id)
            self.table_config = table.config.copy()
        except:
            await self.close()
            return
        
        await self.connect_to_table(self.table_id)
        self.recv_task = asyncio.create_task(self.beggin_recv())
        await self.accept()
        return

    #TODO: write the function.
    async def connect_to_table(self, table_id):
        self.table_connection: websockets.client.ClientConnection = await websockets.client.connect(f"ws://localhost:8765/table/{table_id}")
        await self.table_connection.send(json.dumps({'type':'connection_request','data': {'user_id':self.user.id, 'table_id':table_id}}))
        
    async def beggin_recv(self):
        """ Recieving updates and responses from table server """
        try:
            while self.table_connection.open:
                message = await self.table_connection.recv()
                await self.recieve_table_message(message)
        finally:
            await self.table_connection.close()

    async def add_table_request(self):
        await self.send_to_table_server()


    async def augment_table_view_update(self, message):
        assert message['type'] == 'table_view_update'
        aug_message = message.copy()
        player_names = {}
        for p in aug_message['data']['shared_data']['players']:
            p['player_name'] = await self.get_player_name(p['user_id'])
            player_names[p['sit']] = p['player_name']

        aug_message['data']['shared_data']['player_names'] = player_names


        if 'winners' in aug_message['data']['shared_data']:
            #add winner names, maybe like player_names: {sit: [name,id]} or something like that
            pass

        return aug_message

    async def recieve_table_message(self, message):
        """recieve updates and responses from the table server"""
        TABLE_MESSAGE_TYPES = ['table_view_update', 'balance_update']
        if type(message) == str:
            message = json.loads(message)
        
        if message['type'] == 'table_view_update':
            aug_message = await self.augment_table_view_update(message)
            await self.send_json(aug_message)

        if message['type'] == 'balance_update':
            # Inside a consumer
            await self.channel_layer.send(
                "balance_update",
                message,
            )
    @database_sync_to_async
    def get_player_name(self, user_id: int) -> str:
        return User.objects.get(id=user_id).get_username()


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
            if consumer_request['data']['type'] == 'join':
                account = await self.get_db_user_account()
                if account.balance < consumer_request['data']['chips']:
                    await self.send_json({
                        'type': 'sit_response',
                        'success': False,
                        'message': 'not enough chips in your account!'
                    })
                    return

            await self.send_to_table_server(consumer_request)
        
        if consumer_request['type'] == 'move_request':
            await self.send_to_table_server(consumer_request)
    
    async def disconnect(self, code):
        await self.table_connection.close()
        await self.close()
    
    @database_sync_to_async
    def get_db_table_by_id(self, table_id: str) -> GameTable:
        return GameTable.objects.get(id=table_id)
    
    @database_sync_to_async
    def get_db_user_account(self) -> UserAccount:
        return UserAccount.objects.get(user=self.user)
