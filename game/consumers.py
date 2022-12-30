from channels.generic.websocket import WebsocketConsumer
from random import randint
import json
from asgiref.sync import async_to_sync



class WSConsumer(WebsocketConsumer):
    def connect(self):
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name, self.channel_name
        )

    def receive(self,text_data=None):
        print(text_data)
        i = randint(0,3)
        guess = json.loads(text_data)['message']
        if guess == str(i):
            self.send(json.dumps({'message':'you won!'}))
        else:
            self.send(json.dumps({'message':'you lose!'}))

    
    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name, self.channel_name
        )