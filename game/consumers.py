from channels.auth import login
from random import randint
from channels.generic.websocket import AsyncJsonWebsocketConsumer, AsyncConsumer
from channels.db import database_sync_to_async
from .models import GameTable, Player
from asgiref.sync import async_to_sync
from django.contrib.auth.models import User, AnonymousUser


class GameConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.table_name = self.scope['url_route']['kwargs']['table_name'] 
        
        #if self.scope['user'].username in await self.get_players(self.table_name):
        await self.accept()
        await self.channel_layer.group_add('table', self.channel_name)
        return await self.channel_layer.send(
            self.channel_name,
            {'type':'send_table_state'}
        )
        
        
        #await self.accept()
    
    async def receive_json(self, content, **kwargs):
        print(content)
        type = content.get("type",None)

        if type == 'card_choice':
            return await self.channel_layer.send(
                'test',
                {
                    'type':'card.choice',
                    'message':content.get('choice',None),
                    'player':content.get('player',None),
                    'channel':self.channel_name,
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
        

    @database_sync_to_async
    def sit_request(self,event):
        print(3)
        table = GameTable.objects.get(table_name=event['table'])
        sit = event['sit']
        if sit==1:
            if table.player1 == None:
                table.player1 = self.scope['user']

            elif table.player1==self.scope['user']:
                table.player1 = None
            table.save()
        if sit==2:
            if table.player2 == None:
                table.player2 = self.scope['user']

            elif table.player2==self.scope['user']:
                table.player2 = None
            table.save()
        
        #print(type(table.players.filter(sit=sit)))
        sit_occupation = table.players.filter(sit=sit)
        #print(sit_occupation[0].user)
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
        table = GameTable.objects.get(table_name=self.table_name)
        print(100)

        players = {p.sit:p.user.username for p in table.players.all()}
        print(players)
        message = {
            'players':players,
            'to_move':table.to_move,
            'winner':table.winner,
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

    async def disconnect(self, code):
        await self.channel_layer.group_discard('table',self.channel_name)
        return await self.close()


class Test(AsyncConsumer):
    
    @database_sync_to_async
    def card_choice(self,event):
        async_to_sync(self.update_table)('table',event['message'],event['player'])
        async_to_sync(self.channel_layer.group_send)(
            'table',
            {
                'type':'send_table_state',
                'message':'',
            }
        )       
    
    @database_sync_to_async
    def update_table(self, table_name, card, player):
        table = GameTable.objects.get(table_name=table_name)
        players = {p.sit:p.user for p in table.players.all()}
        # print(table.__dict__)
        print(player)
        
        if table.moves_made == 2:
            if (table.card1 + table.card2) % 2 == 0:
                table.winner = players[1].username
            else:
                table.winner = players[2].username
            table.moves_made += 1
            table.save()
            return
        
        elif table.moves_made in [0,1]:
            p_number = 'p1' if player==players[1].username else 'p2'
            
            if p_number == table.to_move:
                if p_number == 'p1':
                    table.card1 = card
                    table.to_move = 'p2'
                elif p_number == 'p2':
                    table.card2 = card
                    table.to_move = 'p1'
                table.moves_made += 1
                table.save()
            return

        elif table.moves_made == 3:
            if table.to_move == 'p1':
                table.to_move = 'p2'
            else:
                table.to_move = 'p1'
            table.winner = 'game ongoing'
            table.card1 = 0
            table.card2 = 0
            table.moves_made=0
            table.save()
            return
        
    