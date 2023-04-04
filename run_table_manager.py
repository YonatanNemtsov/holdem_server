import os
import django
import asyncio
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "guessing_game.settings")
django.setup()
channel_layer = get_channel_layer()

async def run():
    await channel_layer.send("table_manager", {'type': 'make_tables'})

asyncio.run(run())