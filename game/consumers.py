from random import randint
from channels.auth import login
from channels.generic.websocket import AsyncJsonWebsocketConsumer, AsyncConsumer
from channels.db import database_sync_to_async
from .models import GameLog, GameTable
from asgiref.sync import async_to_sync
from django.contrib.auth.models import User, AnonymousUser


class GameConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.table_name = self.scope['url_route']['kwargs']['table_name'] 
        
        if self.scope['user'].username in await self.get_players(self.table_name):
            await self.accept()
            await self.channel_layer.group_add('table', self.channel_name)
            await self.channel_layer.send(
                'test',
                {
                    'type':'connection.message',
                    'message':'Hello',
                    'channel_name':self.channel_name,
                    'user':self.scope['user'].username
                }

            )
            return
        await self.accept()
        
        #return await self.close()
    
    async def receive_json(self, content, **kwargs):
        print(content)
        type = content.get("type",None)

        if type == 'card_choice':
            await self.channel_layer.send(
                'test',
                {
                    'type':'card.choice',
                    'message':content.get('choice',None),
                    'player':content.get('player',None),
                    'channel':self.channel_name,
                }
            )
        if type == 'sit_request':
            print(1)
            k = await self.channel_layer.send(
                self.channel_name,
                {
                    'type':'sit.request',
                    'table':self.table_name,
                    'sit':content.get('sit',None),
                    'player':content.get('player',None),
                    'channel':self.channel_name,
                }
            )
            print(k)
        return 
    @database_sync_to_async
    def sit_request(self,event):
        print(3)
        table = GameTable.objects.get(table_name=event['table'])
        if event['sit']==1:
            if table.player1 == None:
                table.player1 = self.scope['user']

            elif table.player1==self.scope['user']:
                table.player1 = None
            table.save()
        if event['sit']==2:
            if table.player2 == None:
                table.player2 = self.scope['user']

            elif table.player2==self.scope['user']:
                table.player2 = None
            table.save()

        
    @database_sync_to_async
    def send_table_state(self):
        pass
        
        

    @database_sync_to_async
    def get_players(self,table_name):
        try:
            table = GameTable.objects.get(table_name=table_name)
        except:
            return
        try:
            return (table.player1.username,table.player2.username)
        except:
            return ()
    
    async def update_table(self,event):
        print(event)
        return await self.send_json(event)

    async def disconnect(self, code):
        await self.channel_layer.group_discard('table',self.channel_name)
        print(1)
        return await self.close()


class Test(AsyncConsumer):
    async def connection_message(self, event):
        print(event)

        return await self.channel_layer.group_send(
            'table',
            {
                'type':'update_table',
                'message':event['message'],
                'player' :event['user'],
            }
            )
    
    @database_sync_to_async
    def card_choice(self,event):
        async_to_sync(self.update_table)('table',event['message'],event['player'])
        table = GameTable.objects.get(table_name='table')
        async_to_sync(self.channel_layer.group_send)(
            'table',
            {
                'type':'update_table',
                'message':table.winner,
            }
        )       
    
    @database_sync_to_async
    def update_table(self, table_name, card, player):
        table = GameTable.objects.get(table_name=table_name)
        print(table.__dict__)
        print(player)
        if table.moves_made == 2:
            if (table.card1 + table.card2) % 2 == 0:
                table.winner = table.player1.username
            else:
                table.winner = table.player2.username
            table.moves_made += 1
            table.save()
            return
        
        elif table.moves_made in [0,1]:
            p_number = 'p1' if player==table.player1.username else 'p2'
            
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
            else:
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
        
    