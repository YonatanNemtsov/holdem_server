from channels.auth import login
from random import randint
from channels.generic.websocket import AsyncJsonWebsocketConsumer, AsyncConsumer
from channels.db import database_sync_to_async
from .models import GameTable, Player
from asgiref.sync import async_to_sync
from django.contrib.auth.models import User, AnonymousUser
from time import sleep

class GameConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.table_name = self.scope['url_route']['kwargs']['table_name'] 
        
        await self.accept()
        #sleep(0.4)
        await self.channel_layer.group_add('table', self.channel_name)
        return await self.channel_layer.send(
            self.channel_name,
            {'type':'send_table_state'}
        )
        
    
    async def receive_json(self, content, **kwargs):
        print(content)
        type = content.get("type",None)

        if type == 'game_request':
            print('game_request')

            # todo: add assertions to verify message.
            return await self.channel_layer.send(
                'test',
                {
                    'type':'game_update',
                    'message':content.get('message',None),
                }
            )
        
        if type == 'sit_request':
            print('sit_request')
            return await self.channel_layer.send(
                self.channel_name,
                {
                    'type':'sit.request',
                    'table':self.table_name,
                    'sit':content.get('sit',None),
                    'player':content.get('player',None),
                    'channel':self.channel_name,
                }
            )
        
    async def disconnect(self, code):
        await self.channel_layer.group_discard('table',self.channel_name)
        return await self.close()

    @database_sync_to_async
    def sit_request(self,event):
        print(3)
        table = GameTable.objects.get(table_name=event['table'])
        sit = event['sit']

        assert type(sit)==int
        assert 0 < sit < 10
        
        sit_occupation = table.players.filter(sit=sit)
        print(table.players)
        print(Player.objects.all())
        if not sit_occupation:
            table.players.create(user=self.scope['user'],sit=sit)
            table.save()
        elif sit_occupation[0].user == self.scope['user']:
            sit_occupation[0].delete()
            table.save()
        
        async_to_sync(self.channel_layer.group_send)(
            self.table_name,
            {'type':'send_table_state'}
        )
        print(11)

    @database_sync_to_async
    def send_table_state(self,event):
        print('sending table state')
        table = GameTable.objects.get(table_name=self.table_name)
        players = {
            p.sit:{
                'username':p.user.username,
                'chips':p.chips,
            } 
            for p in table.players.all()
        }
        print(players)
        
        try:
            sit = str(list({i for i in players if players[i]['username']==self.scope['user'].username})[0])
            card = table.cards[sit]
        except:
            sit =None
            card =None

        print(sit,card)
        message = {
            'players':players,
            'to_move':table.to_move,
            'winner':table.winner,
            'card':card,
            'sit':sit,
            
        }

        async_to_sync(self.send_json)(
            {
                'type': 'table_state',
                'message': message
            }
        )
    
    @database_sync_to_async
    def get_players(self,table_name):
        table =  GameTable.objects.get(table_name)
        players = [player.user.username for player in table.players.all()]
        return players

class Test(AsyncConsumer):

    @database_sync_to_async
    def game_update(self, event):
        action = event['message']['action']

        if action == 'start_round':
            print('start round request recieved')
        if action == 'bet':
            print(f'bet { event["message"]["amount"]} request recieved')
        if action == 'raise':
            print(f'raise {event["message"]["amount"]} request recieved')
        if action == 'call':
            print('call request recieved')
        if action == 'fold':
            print('fold request recieved')
        if action =='check':
            print('check request recieved')

        """
        table = GameTable.objects.get(table_name=table_name)
        pl = {p.sit:p.user for p in table.players.all()}
        players = table.players.all()
        table.first_to_move = min(pl.keys())
        table.make_queue()
        table.save()
       """ 

        # print(table.__dict__)
    
       