
from random import randint
import json

from asgiref.sync import async_to_sync
from channels.auth import login
from channels.generic.websocket import WebsocketConsumer


class WSConsumer(WebsocketConsumer):

    def connect(self):
        
        self.user = self.scope["user"]
        print(self.user.username)
        self.group_name = 'a'
        async_to_sync(self.channel_layer.group_add)(
            self.group_name, self.channel_name
        )

        self.accept()

    def receive(self,text_data=None):

        i = randint(0,3)
        guess = json.loads(text_data)['message']

        if guess == str(i):
            message = 'you won!'
        else:
            message = 'you lose!'
        
        json_message = {"type": "game_message",'message':message}

        async_to_sync(self.channel_layer.group_send)(
            self.group_name, json_message
        )


    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name, self.channel_name
        )

    def game_message(self, event):
        message = event["message"]
        # Send message to WebSocket
        self.send(text_data=json.dumps({"message": message}))

