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
        self.db_connection = None # websocket connection

    def add_table(self, table_id: int, config: dict):
        #TODO: check if table exists, validate, etc.
        self.tables[table_id] = TableManager(table_id, config)
    
    async def run_tables(self):
        while True:
            for table in self.tables.values():
                if not table.running:
                    asyncio.create_task(table.run_table())
            await asyncio.sleep(5)

    #TODO: implement
    async def graceful_shutdown(self):
        pass

    async def handle_db_conection_request(self, request: dict, websocket: 'websocket'):
        self.db_connection = websocket
        print('Database connected')
        return json.dumps({'type':'db_connection_response','success':True})

    async def handle_request(self, request: dict, websocket: 'websocket') -> dict:
        #print(request)
        request = json.loads(request)

        if request['type'] == 'db_connection_request':
            return (await self.handle_db_conection_request(request, websocket))
        
        table = self.tables[request['data']['table_id']]
        response = await table.handle_request(request, websocket)

        if request['type'] == 'sit_request' and json.loads(response)['success'] == True:

            await self.db_connection.send(json.dumps({
                'type':'balance_update',
                'data': {
                    'user_id': request['data']['user_id'],
                    'table_id': request['data']['table_id'],
                    'amount': json.loads(response)['data']['amount'], #for experiment
                    'action': request['data']['type'],
                }
            }))

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
            await asyncio.sleep(0.5)
            if self.table.round == None and len(self.table.players) > 1:
                self.table.start_new_round()
                self.table.round.start()
                await self.send_table_view_to_all()
            
            elif self.table.round != None:
                if self.table.round.stage == HoldemRoundStage.ENDED:
                    await asyncio.sleep(3)
                    
                    if len(self.table.players) < 2:
                        # wait for more players to join
                        await self.send_table_view_to_all()
                        continue
                    
                    self.table.start_new_round()
                    self.table.round.start()
                    await self.send_table_view_to_all()
                if self.table.round.stage in [HoldemRoundStage.SHOWDOWN, HoldemRoundStage.NO_SHOWDOWN]:
                    self.table.round.make_pots()
                    self.table.round.determine_pots_winners()
                    self.table.round.distribute_pots()
                    #(p.sync_chips() for p in self.table.players)
                    await asyncio.sleep(2)
                    await self.send_table_view_to_all()
                    self.table.round.start_next_move()
                    await self.send_table_view_to_all()
    
    #TODO: Implement
    async def graceful_shutdown(self):
        pass
    
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
        
        # TODO: move to run_table
        if response['success'] == True:
            if len(self.table.round.move_queue) == 0:
                await self.send_table_view_to_all()
                self.table.round.make_pots()
                #(p.sync_chips() for p in self.table.players)
                await asyncio.sleep(1.5)
                #self.table.round.start_next_move()

            elif len([p for p in self.table.round.players if not p.folded]) == 1:
                self.table.round.start_next_move()
                await self.send_table_view_to_all()
                self.table.round.make_pots()
                await asyncio.sleep(1.5)
                #self.table.round.start_next_move()
            
            self.table.round.start_next_move()
        
        await self.send_table_view_to_all()
        
        return response
    
    async def _handle_connection_request(self, request: dict, websocket) -> dict:
        # save connection in self.connections
        await self.add_connection(websocket, request['data']['user_id'])
        view = json.dumps(await self.get_table_view(request['data']['user_id']))
        await websocket.send(view)
        return {'type':'connection_response','success': True}
    
    async def _handle_table_view_request(self, request: dict, websocket) -> dict:
        return await self.get_table_view(request['data']['user_id'])
        
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
        
        #await self.send_table_view_to_all()

        return json.dumps(response)
    
    async def add_connection(self, websocket, user_id: int) -> None:
        #print(self.connections)
        if user_id in self.connections:
            if (ws := self.connections[user_id]).open:
                await ws.close()
            
        self.connections[user_id] = websocket
    
    async def remove_connection(self, websocket, user_id: int) -> None:
        assert user_id in self.connections

        if self.connections[user_id].open:
            await self.connections[user_id].close()
        
        del self.connections[user_id]

    async def get_table_view(self, user_id: int):
        return self.table.get_table_view(self.table.get_player_by_id(user_id))
    
    async def send_table_view_to_all(self):
        for user_id in self.connections:
            if not self.connections[user_id].open:
                continue
            table_view = await self.get_table_view(user_id)
            await self.connections[user_id].send(json.dumps(table_view))