from dataclasses import dataclass
from holdem_core.core_game.holdem_table import HoldemTable,HoldemTableConfig,HoldemTablePlayer
from holdem_core.core_game.holdem_round import HoldemRoundStage
import asyncio
from websockets.server import serve
import json

class TableServerManager:
    """
    NOT FOR USE ANYMORE

    This class is responsible for managing and running the poker tables
    of the server. It adds tables, manages their state, and handles player requests.
    """

    def __init__(self):
        self.tables: dict[int, HoldemTable] = dict()
        self.connections = dict() # user_id: connection
    
    async def add_table(self, table_id: int, config: dict):
        conf = HoldemTableConfig(**config)
        self.tables[table_id] = HoldemTable(table_id, conf)
    


@dataclass
class TableManagerConnection:
    user_id: int
    websocket: object # websocket object
    status: bool # 1 is active 0 not

class TableManager:
    """
    This class is responsible for managing and running a poker table.
    It manages its state, and handles player requests.
    """
    def __init__(self) -> None:
        self.table = HoldemTable(1,HoldemTableConfig(1,0,100,1000,9))
        self.connections = dict() # websocket connections, keys are user_id's

    async def run_table(self):
        while True:
            await asyncio.sleep(1)
            if self.table.round == None and len(self.table.players) > 1:
                self.table.start_new_round()
                self.table.round.start()
                for user_id in self.connections:
                    table_view = await self.get_table_view(self.table.table_id, user_id)
                    await self.connections[user_id].send(json.dumps(table_view))
            
            elif self.table.round != None:
                if self.table.round.stage == HoldemRoundStage.ENDED:
                    self.table.start_new_round()
                    self.table.round.start()
                    for user_id in self.connections:
                        table_view = await self.get_table_view(self.table.table_id, user_id)
                        await self.connections[user_id].send(json.dumps(table_view))
                
                if self.table.round.stage in [HoldemRoundStage.SHOWDOWN, HoldemRoundStage.NO_SHOWDOWN]:
                    self.table.round.make_pots()
                    self.table.round.determine_pots_winners()
                    print('winners: ', self.table.round.winners)
                    self.table.round.distribute_pots()
                    self.table.round.start_next_move()
                    for user_id in self.connections:
                        table_view = await self.get_table_view(self.table.table_id, user_id)
                        await self.connections[user_id].send(json.dumps(table_view))
    
    # TODO: implement refactoring
    # Request sub handlers
    async def _handle_sit_request(self, request: dict, websocket) -> dict:
        # add player to self.table.players if valid
        #TODO: ugly, to be improved
        if request['data']['type'] == 'leave':
            player = self.table.get_player_by_id(request['data']['user_id'])
            if player == None:
                response = {'type':'sit_response','success': False}
            
            else:
                request['data']['sit'] = player.sit
                response = self.table.process_sit_request(request['data'])
        
        elif request['data']['type'] == 'join':
            response = self.table.process_sit_request(request['data'])
        
        return response
    
    async def _handle_move_request(self, request: dict, websocket) -> dict:
        if self.table.round == None:
            return {'type':'move_response','success': False}
        
        req = request.copy()
        req['data'].update({'sit':self.table.get_player_by_id(req['data']['user_id']).sit})
        response = self.table.request_handler(request)
        print(response)
        if response['success'] == True:
            if len(self.table.round.move_queue) == 0:
                self.table.round.make_pots()
            self.table.round.start_next_move()
        
        return response
    
    async def _handle_connection_request(self, request: dict, websocket) -> dict:
        # save connection in self.connections
        await self.add_connection(websocket, request['data']['user_id'])
        return {'type':'connection_response','success': True}
    
    async def _handle_table_view_request(self, request: dict, websocket) -> dict:
        return await self.get_table_view(request['data']['table_id'], request['data']['user_id'])
        
    async def _handle_add_chips_request(self, request: dict, websocket) -> dict:
        pass

    async def handle_request(self, request: dict, websocket: 'websocket'):
        
        """ Handles all requests initiated by a consumer to the table server 
        requests are of the form:

        {
            'type': str,
            ...

        }
        """
        
        HANDLE = {
            'connection_request': self._handle_connection_request,
            'sit_request': self._handle_sit_request,
            'table_view_request': self._handle_table_view_request,
            'move_request': self._handle_move_request,
            'add_chips_request': self._handle_add_chips_request,
        }

        print(self.table.round)
        if type(request) == str:
            request = json.loads(request)
        
        assert request['type'] in HANDLE.keys()

        response = await HANDLE[request['type']](request, websocket)

        if response['success'] == False:
            return json.dumps(response)
        
        for user_id in self.connections:
            table_view = await table_manager.get_table_view(table_manager.table.table_id, user_id)
            await table_manager.connections[user_id].send(json.dumps(table_view))


        return json.dumps(response)
    

    async def add_connection(self, websocket, user_id: int) -> None:
        if user_id in self.connections:
            if ws := self.connections[user_id].open:
                ws.close()
            
        self.connections[user_id] = websocket
    
    async def remove_connection(self, websocket, user_id: int) -> None:
        assert user_id in self.connections

        if self.connections[user_id].open:
            self.connections[user_id].close()
        
        del self.connections[user_id]

    async def get_table_view(self, table_id: int, user_id: int):
        return self.table.get_table_view(self.table.get_player_by_id(user_id))

table_manager = TableManager()

async def table_server(websocket, path):

    async for message in websocket:
        print(message)
        response = await table_manager.handle_request(message, websocket)
        await websocket.send(response)

        for user_id in table_manager.connections:
            table_view = await table_manager.get_table_view(table_manager.table.table_id, user_id)
            await table_manager.connections[user_id].send(json.dumps(table_view))

async def server():
    async with serve(table_server, "localhost", 8765):
        await asyncio.Future()  # run forever

async def main():
    server_task = asyncio.create_task(server())
    table_task = asyncio.create_task(table_manager.run_table())
    await asyncio.gather(server_task, table_task)


if __name__ == '__main__':
    asyncio.run(main())