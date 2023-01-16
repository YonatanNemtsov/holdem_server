
from random import randint
import json

from asgiref.sync import async_to_sync
from channels.auth import login
from channels.generic.websocket import WebsocketConsumer
from channels.db import database_sync_to_async

from .models import GameLog, GameTable




class WSConsumer(WebsocketConsumer):

    def connect(self):

        # check if user is player1 or player2, and if he is authenticated,
        # and then accept connection.

        self.table_name = self.scope['url_route']['kwargs']['table_name']
        self.user = self.scope['user']

        table = self.get_table(self.table_name)

        try:
            if self.user in [table.player1, table.player2]:
                print(self.user)
                async_to_sync(login)(self.scope,self.user)
                print(self.user.username)
                #lf.scope["session"].save()
        except:
            self.disconnect(code=1)
            return

        async_to_sync(self.channel_layer.group_add)(
            self.table_name, self.channel_name
        )
        self.accept()

        # change status to connected
        if self.user == table.player1:
            table.p1_status = 1
            self.sit = 1
        elif self.user == table.player2:
            table.p2_status = 1
            self.sit = 2
        table.save()
        login_m = {
            'type':'login_message',
            'message':'connected',
            'user':self.user.username,
            'channel_name':self.channel_name
        }

        self.send(text_data=json.dumps(table.log))
        async_to_sync(self.channel_layer.group_send)(
            self.table_name, login_m
        )

        return

    def receive(self,text_data=None):
        message = json.loads(text_data)
        if message['type'] == 'new_move':
            print('new_move')
            json_message = {
                "type": "new_move",
                'message':f'player {self.sit} chose {message["message"]}',
                'user':self.user.username
            }

            async_to_sync(self.channel_layer.group_send)(
                self.table_name,
                json_message
            )
        if message['type'] == 'resign':
            print('resign')
            json_message = {
                "type": "resign",
                'message': f'player {self.sit} resigned.',
                'user':self.user.username
            }
            async_to_sync(self.channel_layer.group_send)(
                self.table_name,
                json_message
            )

    def disconnect(self, code=None):
        if code == 1:
            self.close()
            return

        json_message = {
            "type": "logout_message",
            'message':f'user {self.user.username} disconnected',
            'user':self.user.username
            }

        async_to_sync(self.channel_layer.group_send)(
            self.table_name,json_message
        )
        async_to_sync(self.channel_layer.group_discard)(
            self.table_name, self.channel_name
        )

    # Helper functions

    def get_game_log(self, table):
        try:
            game_log = GameLog.objects.get(table=table)
        except:
            game_log = GameLog.objects.create()
            game_log.table = table
            game_log.save()
        
        return game_log

    def get_table(self, table):
        try:
            game_table = GameTable.objects.get(table_name=table)
        except:
            raise NameError(f'table {table} not found!')
        return game_table

    def send_game_state(self):
        table_log=self.get_table(self.table_name).log
        print(table_log)
        json_message = {
            'type':'game_state',
            'message':table_log,
            'user':self.user.username
        }
        self.send(text_data=json.dumps(json_message))

    # Handlers
    
    def new_move(self, event):
        print(event)
        self.send(text_data=json.dumps(event))
        self.send_game_state()

    def login_message(self, event):
        print(event)
        self.send(text_data=json.dumps(event))
        self.send_game_state()

    def logout_message(self, event):
        print(event)
        self.send(text_data=json.dumps(event))
        self.send_game_state()

    def resign(self, event):
        print(event)
        self.send(text_data=json.dumps(event))
        self.send_game_state()