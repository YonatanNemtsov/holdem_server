import asyncio
import json
import os
from websockets.server import serve
from table_manager import TableManager, TableServerManager


import django


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "guessing_game.settings")

django.setup()

from game.models import GameTable

tables = GameTable.objects.all()


table_server_manager = TableServerManager()


for table in tables:
    table_server_manager.add_table(table.id, table.config)

async def table_server(websocket, path):
    async for message in websocket:

        response = await table_server_manager.handle_request(message, websocket)
        if json.loads(message)['type'] == 'db_connection_request':
            pass
            #await websocket.send(response)
        
        await websocket.send(response)

async def server():
    async with serve(table_server, "localhost", 8765):
        await asyncio.Future()  # run forever

async def main():
    server_task = asyncio.create_task(server())
    table_task = asyncio.create_task(table_server_manager.run_tables())
    await asyncio.gather(server_task, table_task)


if __name__ == '__main__':
    asyncio.run(main())