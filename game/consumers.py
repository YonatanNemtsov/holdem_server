from channels.generic.websocket import WebsocketConsumer
from random import randint
import json
from time import sleep

class WSConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()

    def receive(self,text_data=None):
        print(text_data)
        i = randint(0,10)
        guess = json.loads(text_data)['message']
        if guess == str(i):
            self.send(json.dumps({'message':'you won!'}))
        else:
            self.send(json.dumps({'message':'you lose!'}))

    
    