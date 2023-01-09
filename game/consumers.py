
from random import randint
import json

from asgiref.sync import async_to_sync
from channels.auth import login
from channels.generic.websocket import WebsocketConsumer
from channels.layers import get_channel_layer

class WSConsumer(WebsocketConsumer):

    def connect(self):
        
        table_name = self.scope['url_route']['kwargs']['table_name']
        try:
            user = self.scope["user"]
            async_to_sync(login)(self.scope,user)
            #print(self.user.username)
        
            self.scope["session"].save()

        except:
            user = self.scope['user']
        
        self.group_name = table_name

        async_to_sync(self.channel_layer.group_add)(
            self.group_name, self.channel_name
        )
        login_m = {'type':'login_message','message':'connected','user':user.username}
        async_to_sync(self.channel_layer.group_send)(
            self.group_name, login_m
        )

        self.accept()

    def receive(self,text_data=None):
        print(get_channel_layer())
        #print(text_data)
        i = randint(0,3)
        guess = json.loads(text_data)['message']

        if guess == str(i):
            message = 'you won!'
        else:
            message = 'you lose!'
        user = self.scope['user']
        json_message = {"type": "game_message",'message':message,'user':user.username}

        async_to_sync(self.channel_layer.group_send)(
            self.group_name, json_message
        )


    def disconnect(self, code):
        user = self.scope['user']
        json_message = {"type": "disconnect_message",'message':f'user {user.username} disconnected' ,'user':user.username}
        async_to_sync(self.channel_layer.group_send)(
            self.group_name,json_message
        )
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name, self.channel_name
        )




    # Handlers
    
    def game_message(self, event):
        # print(event)
        # Send message to WebSocket
        self.send(text_data=json.dumps(event))

    def login_message(self, event):
        self.send(text_data=json.dumps(event))

    def disconnect_message(self, event):
        self.send(text_data=json.dumps(event))