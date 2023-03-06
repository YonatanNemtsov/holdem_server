from channels.generic.websocket import AsyncJsonWebsocketConsumer, AsyncConsumer
from channels.db import database_sync_to_async
from asgiref.sync import async_to_sync
from django.contrib.auth.models import User

import deuces.deuces as hand_ranker
import itertools
from random import shuffle, randint
from time import sleep
from .models import GameTable, Player, UserAccount

class GameConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.table_name = self.scope['url_route']['kwargs']['table_name'] 
        print(self.scope['user'].id, self.scope['user'].username)

        
        await self.accept()
        #sleep(0.4)
        await self.channel_layer.group_add(self.table_name, self.channel_name)
        await self.channel_layer.send(
            self.channel_name,
            {'type':'send_table_state'}
        )
        return 
    
    async def receive_json(self, content, **kwargs):
        print(content)

        type = content.get("type",None)
        if type == 'game_request':
            print('game_request')

            # todo: add assertions to verify message.
            await self.channel_layer.send(
                'test',
                {
                    'type':'game_update',
                    'table':self.table_name,
                    'user_id':self.scope['user'].id,
                    'message':content.get('message',None),
                    
                }
            )
        
        if type == 'start_hand_request':
            await self.channel_layer.send(
                'test',
                {
                    'type':'start_new_hand',
                    'table':self.table_name,
                    'user_id':self.scope['user'].id,
                    'message':content.get('message',None),
                }
            )
        
        if type == 'sit_request':
            print('sit_request')
            await self.channel_layer.send(
                self.channel_name,
                {
                    'type':'sit.request',
                    'table':self.table_name,
                    'sit':content.get('sit',None),
                    'player':content.get('player',None),
                    'amount':content.get('amount',None),
                    'channel':self.channel_name,
                }
            )
        
        return
        
    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.table_name,self.channel_name)
        return await self.close()

    @database_sync_to_async
    def sit_request(self,event):
        print(3)
        table = GameTable.objects.get(table_name=event['table'])
        sit = event['sit']
        amount = event['amount']
        if table.table_state != 0:
            print("can't sit, game is ongoing")
            return
        assert amount > table.MIN_CHIPS_TO_SIT
        assert type(sit) == int
        assert 0 < sit < 10
        
        user_account = UserAccount.objects.get(user=self.scope['user'])
        sitting_player = table.players.filter(sit=sit)
        
        print(table.players)
        print(Player.objects.all())
        if not sitting_player:
            player = table.players.create(user=self.scope['user'], sit=sit, chips=amount, table_name=table.table_name)
            user_account.balance -= amount
            user_account.save()
            table.save()
        elif sitting_player[0].user == self.scope['user']:
            user_account.balance += sitting_player[0].chips
            user_account.save()
            sitting_player[0].delete()
            table.save()
        print(user_account.balance)
        
        async_to_sync(self.channel_layer.group_send)(
            self.table_name,
            {'type':'send_table_state'}
        )

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
        
        try:
            sit = str(list({i for i in players if players[i]['username']==self.scope['user'].username})[0])
            card = table.cards[sit]
        except:
            sit = ''
            card = None
        
        show_cards = dict()
        if table.table_state == 0:
            if len([p for p in table.move_queue['has_folded'] if not table.move_queue['has_folded'][p]])>1:
                for sit in players:
                    print(table.move_queue['has_folded'])
                    if not table.move_queue['has_folded'][str(sit)]:
                        show_cards[sit] = table.cards[str(sit)]

        winners = dict()
        message = {
            'players': players,
            'table_state': table.table_state,
            'turn': table.move_queue['queue'][table.move_index],
            'pots': table.pots,
            'card': card,
            'community_cards': table.community_cards,
            'sit': sit,
            'last_moves': get_players_last_moves(table),
            'event': event,
            'show_cards': show_cards,
            'winners': table.winners,
            'has_folded': table.move_queue['has_folded']
        }

        async_to_sync(self.send_json)(
            {
                'type': 'table_state',
                'message': message
            }
        )



def get_player_total_bet_in_round(round_bets: list, player_sit: int) -> int:
    return [player_sit ,sum([0]+[bet[2] for bet in round_bets if bet[0]==player_sit])]

def get_player_total_bet(bets: dict, player_sit: int) -> int:

    return [player_sit,sum((
        get_player_total_bet_in_round(bets[round], player_sit)[1]
        for round in bets.keys()
    ))]

def get_call_amount(table:GameTable, player:Player) -> int:
        if not table.bets[str(table.table_state)]:
            return 0
        player_bet_in_round = get_player_total_bet_in_round(table.bets[str(table.table_state)],player.sit)
        amount_to_call = max(((get_player_total_bet_in_round(table.bets[str(table.table_state)], p.sit)) for p in table.players.all()), key=lambda x:x[1])
        return amount_to_call[1] - player_bet_in_round[1]

def get_min_raise_amount(table: GameTable) -> int:
        if not table.bets[str(table.table_state)]:
            return table.BIG_BLIND*2
        min_raise_amount = 2 * max([bet[2] for bet in table.bets[str(table.table_state)] if bet[1]=='raise']+[0])
        return min_raise_amount

def get_players_last_moves(table: GameTable) -> dict:
    if table.table_state == 0:
        return dict()
    moves_in_round = table.bets[str(table.table_state)]
    last_moves = dict()
    for move in moves_in_round:
        print(move)
        last_moves[move[0]] = [move[1],move[2]]
    return last_moves

def make_pots(bets: list[list], player_sits: list[int]) -> dict:
    ordered_total_bets = sorted([get_player_total_bet(bets, sit) for sit in player_sits], key=lambda x:x[1])
    pots = dict()
    min = 0
    for count,(player,bet) in enumerate(ordered_total_bets):
        if bet > min:
            pots[bet] = {'pot':(bet-min) * (len(ordered_total_bets) - count),'players':[]}
            min = bet
        for bet_rank in pots:
            pots[bet_rank]['players'].append(player)
    return pots

def determine_winners(players: list[Player], table: GameTable) -> list[Player]:

    print(players)
    not_folded_players = [p for p in players if not table.move_queue['has_folded'][str(p.sit)]]
    if len(not_folded_players) == 1:
        return [not_folded_players[0]]
    
    evaluator = hand_ranker.Evaluator()
    hand_ranks = dict()
    for p in not_folded_players:
        cards = [hand_ranker.Card.new(c) for c in table.cards[str(p.sit)]]
        hand_ranks[p.sit] = evaluator.evaluate(cards, [hand_ranker.Card.new(c) for c in table.community_cards])
        
    winners = [p for p in not_folded_players if p.sit == min(hand_ranks,key=hand_ranks.get)]

    print(winners)
    return winners

def distribute_pot(table: GameTable):
    table.winners = dict()
    for bet_rank in table.pots:
        players = [p for p in table.players.all() if p.sit in table.pots[bet_rank]['players']]
        winners = determine_winners(players,table)
        for winner in winners:
            if winner.sit in table.winners:
                table.winners[winner.sit] += table.pots[bet_rank]['pot']//len(winners)
            else: 
                table.winners[winner.sit] = table.pots[bet_rank]['pot']//len(winners)
            winner.chips += table.pots[bet_rank]['pot']//len(winners)
            winner.save()
    
    table.pots = dict()
    table.save()

def start_next_betting_round(table: GameTable):
    print(table.table_state)
    table.pots = make_pots(table.bets,table.move_queue['order'])
    print(table.pots)
    if table.table_state == table.TableState.RIVER:
        table.table_state = table.TableState.ENDED
        distribute_pot(table)
        table.save()
        return

    table.move_queue['order'] = sorted([
        p.sit for p in table.players.all() if not table.move_queue['has_folded'][str(p.sit)] 
    ])
    table.move_queue['queue'] = table.move_queue['order'].copy()

    table.table_state += 1
    if table.table_state == table.TableState.FLOP:
        table.community_cards += [table.deck.pop() for i in range(3)]
    if table.table_state in [table.TableState.TURN, table.TableState.RIVER]:
        table.community_cards += [table.deck.pop()]
    table.move_index = 0


class Test(AsyncConsumer):

    def fold_request(table: GameTable, player: Player, message: dict) -> None:
        fold_is_valid = True
        if not fold_is_valid:
            return
        
        table.move_queue['has_folded'][str(player.sit)] = True
        table.bets[str(table.table_state)].append([player.sit, 'fold', 0])
        print(table.move_queue)
        if len(players_left := [sit for sit in table.move_queue['order'] if not table.move_queue['has_folded'][str(sit)]]) == 1:
            print(players_left)
            # idea: refactor to declare_winner(table),
            table.table_state = table.TableState.ENDED
            table.pots = make_pots(table.bets,table.move_queue['order'])
            distribute_pot(table)
            return
        
        if table.move_index == len(table.move_queue['queue']) - 1:
            start_next_betting_round(table)
        else:
            table.move_index += 1
        table.save()

    def bet_request(table: GameTable, player: Player, message: dict) -> None:
        pass
    
    def raise_requset(table: GameTable, player: Player, message : dict) -> None:
        amount = int(message["amount"])
        raise_is_valid = (player.chips >= amount >= get_min_raise_amount(table))

        if not raise_is_valid:
            return

        table.bets[str(table.table_state)].append([player.sit,'raise',amount])
        player.chips -= amount
        player.save()
        # table.pots = make_pots(table.bets,table.move_queue['order'])
        move_sit = table.move_queue['queue'][table.move_index]
        remaining_players_in_queue = table.move_queue['queue'][table.move_index+1:]
        table.move_queue['queue'] += (
            [
                p for p in (
                    table.move_queue['order'][:table.move_queue['order'].index(move_sit)] + 
                    table.move_queue['order'][table.move_queue['order'].index(move_sit)+1:]
                )
                if not p in remaining_players_in_queue
            ]
        )
    
        table.move_index += 1
        table.save()
    
    def call_requset(table: GameTable, player: Player, message: dict ) -> None:
        
        call_amount = min(player.chips, get_call_amount(table,player))
        table.bets[str(table.table_state)].append([player.sit, 'call', call_amount])
        player.chips -= call_amount
        player.save()
        # table.pots = make_pots(table.bets,table.move_queue['order'])
        if table.move_index == len(table.move_queue['queue']) - 1:
            print('next round starting')
            start_next_betting_round(table)
            table.save()
            return
        table.move_index += 1
        table.save()
        
    def check_requset(table: GameTable, player: Player, message: dict) -> None:
        if get_call_amount(table,player) > 0:
            print("Check not allowed. Call, Raise, or Fold.")
            return

        table.bets[str(table.table_state)].append([player.sit, 'check', 0])
        table.save()
        if table.move_index == len(table.move_queue['queue']) - 1:
            print('next round starting')
            start_next_betting_round(table)
            table.save()
            return
        table.move_index += 1
        table.save()

    MOVE_FUNCTIONS = {
            (FOLD:='fold'): fold_request,
            (RAISE:='raise'): raise_requset,
            (CALL:='call'): call_requset,
            (CHECK:='check'): check_requset,
        }

    @database_sync_to_async
    def game_update(self, event: dict) -> None:
        
        # parse message info
        message = event['message']
        action = message['action']
        table = GameTable.objects.get(table_name=event['table'])
        player = table.players.get(user=User.objects.get(id=event['user_id']))
        print(table.move_index,table.move_queue['queue'])
        print(table.move_queue['order'])
        # verification 
        if table.table_state == 0:
            print('hand ended! move is not allowed')
            return
        if table.move_queue['queue'][table.move_index] != player.sit:
            print(f"not {player.user.username}'s turn")
            return
        
        # apply move
        print(action, (message["amount"] if 'amount' in message else ''), 'request recieced')
        self.MOVE_FUNCTIONS[action](table, player, message)
        print(table.bets)
        
        # send updated table to clients
        async_to_sync(self.channel_layer.group_send)(
                    table.table_name,
                    {
                        'type':'send_table_state',
                        'message':dict()
                    }
                )
        return

    

    def start_new_hand_request(self,table: GameTable, player: Player, message: dict) -> None:

        if table.table_state != table.TableState.ENDED:
            print("can't start round: game is ongoing")
            return
        table.make_move_queue()
        table.deck = create_deck()
        table.cards = deal_cards(table)
        table.bets = GameTable.init_bets()
        table.community_cards = []
        table.table_state = table.TableState.PREFLOP
        table.pots = dict()
        table.winners = dict()
        table.save()
    
    @database_sync_to_async
    def start_new_hand(self,event: dict) -> None:
        
        # parse message info
        message = event['message']
        table = GameTable.objects.get(table_name=event['table'])
        player = table.players.get(user=User.objects.get(id=event['user_id']))
        if len(table.players.all())==1:
            print("can't start round, need at least two players")
            return 
        print('new hand request recieved')

        # start new hand
        self.start_new_hand_request(table,player,message)

        # send updated table to clients
        async_to_sync(self.channel_layer.group_send)(
                    table.table_name,
                    {
                        'type':'send_table_state',
                        'message':dict(),
                    }
                )
        return

def deal_cards(table: GameTable):
        sits_occupied = [p.sit for p in table.players.all()]
        cards = {sit:[table.deck.pop() for i in range(2)] for sit in sits_occupied}
        return cards 

def create_deck():
    suites = ['h','d','c','s']
    ranks = ['2','3','4','5','6','7','8','9','T','J','Q','K','A']
    shuffle(deck:=list(p[0]+p[1] for p in itertools.product(ranks,suites)))
    return deck