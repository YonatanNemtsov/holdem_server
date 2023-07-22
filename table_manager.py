from holdem_core.core_game.holdem_table import HoldemTable,HoldemTableConfig
from holdem_core.core_game.holdem_round import HoldemRoundStage
import asyncio
import json

class TableServerManager:
    """
    This class is responsible for managing and running the poker tables
    of the server. It adds tables (TableManager objects), and routes requests to 
    TableManager objects.
    """

    def __init__(self):
        self.tables: dict[int, TableManager] = dict()
        self.connections = dict() # user_id: connection
    
    def add_table(self, table_id: int, config: dict):
        #TODO: check if table exists, validate, etc.
        self.tables[table_id] = TableManager(table_id, config)
    
    async def run_tables(self):
        while True:
            for table in self.tables.values():
                if not table.running:
                    asyncio.create_task(table.run_table())
            await asyncio.sleep(5)

    async def handle_request(self, request: dict, websocket: 'websocket') -> dict:
        request = json.loads(request)
        table = self.tables[request['data']['table_id']]
        response = await table.handle_request(request, websocket)
        return response


class TableManager:
    """
    This class is responsible for managing and running a poker table.
    It manages its state, and handles player requests.
    """
    def __init__(self, table_id: str, table_config: dict) -> None:
        self.table = HoldemTable(table_id ,HoldemTableConfig(**table_config))
        self.connections = dict() # websocket connections, keys are user_id's
        self.running = False

    # TODO: Refactor and improve, add timers, add default moves, etc.
    async def run_table(self):
        self.running = True
        while True:
            await asyncio.sleep(1)
            if self.table.round == None and len(self.table.players) > 1:
                self.table.start_new_round()
                self.table.round.start()
                await self.send_table_view_to_all()
            
            elif self.table.round != None:
                if self.table.round.stage == HoldemRoundStage.ENDED:
                    self.table.start_new_round()
                    self.table.round.start()
                    await self.send_table_view_to_all()
                
                if self.table.round.stage in [HoldemRoundStage.SHOWDOWN, HoldemRoundStage.NO_SHOWDOWN]:
                    self.table.round.make_pots()
                    self.table.round.determine_pots_winners()
                    self.table.round.distribute_pots()
                    self.table.round.start_next_move()
                    await self.send_table_view_to_all()
    
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

        if type(request) == str:
            request = json.loads(request)
        
        assert request['type'] in HANDLE.keys()

        response = await HANDLE[request['type']](request, websocket)

        if response['success'] == False:
            return json.dumps(response)
        
        await self.send_table_view_to_all()

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
    
    async def send_table_view_to_all(self):
        for user_id in self.connections:
            if not self.connections[user_id].open:
                continue
            table_view = await self.get_table_view(self.table.table_id, user_id)
            await self.connections[user_id].send(json.dumps(table_view))