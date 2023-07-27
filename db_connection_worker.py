import os
import asyncio
import json
import websockets.client

import django
from channels.db import database_sync_to_async


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "guessing_game.settings")

django.setup()

from game.models import UserAccount



class BalanceUpdateWorker:
    def __init__(self):
        self.connection = None # websocket

    async def connect_to_table_server(self):
        self.connection: websockets.client.ClientConnection = await websockets.client.connect("ws://localhost:8765/database_connection/")
        await self.connection.send(json.dumps({'type':'db_connection_request', 'data':{}}))
        #print(await self.connection.recv())

    async def run(self):
        try:
            while True:
                request = json.loads(await self.connection.recv())
                if request['type'] == 'balance_update':
                    print(request)
                    await self.update_balance(request)
        finally:
            await self.connection.close()
    
    @database_sync_to_async
    def update_balance(self, request: dict):
        """balance update requests are of the form:
        {
            'type': 'balance_update',
            'data': {
                'user_id': str,
                'table_id':str,
                'action': 'game_withdrawl'/'game_deposit/'game_update'
                'amount': int,
            }
        }
        
        """
        # TODO: Make chips_in_action, in the UserAccount model a dict, 
        # with table id's as keys, for better tracking.

        account = UserAccount.objects.get(id=request['data']['user_id'])

        sign = 1 if request['data']['action'] == 'leave' else -1
        account.balance += sign * request['data']['amount']

        #TODO: chips_in_action needs to be updated every round, ('game_update')
        #account.chips_in_action -= sign * request['data']['amount']
        
        account.save()
        print(account.balance, account.chips_in_action)

async def main():
    worker = BalanceUpdateWorker()
    await worker.connect_to_table_server()
    await worker.run()

if __name__ == '__main__':
    asyncio.run(main())