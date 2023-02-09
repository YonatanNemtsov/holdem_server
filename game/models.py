from django.db import models
from django.contrib.auth.models import User

from random import randint
# Create your models here.


class Player (models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    sit = models.IntegerField()
    chips = models.IntegerField(default=100)
    def __str__(self):
        return f'{self.sit} {self.user.username}'

class GameTable(models.Model):
    # need to rewrite more elegantly.
    table_name = models.CharField(max_length=100,default='table',unique=True)

    players = models.ManyToManyField(
        Player,
    )
    
    first_to_move = models.IntegerField(default=1)
    move_index = models.IntegerField(default=0)
    # player_status = models.JSONField(default=dict)
    def make_move_queue(self):
        queue = {
            'has_folded':{
                p.sit:False
                for p in sorted((self.players.all()), key=lambda x: x.sit)
            },

            # todo: make queue depend also on first to move
            'queue':[
                p.sit for p in sorted((self.players.all()), key=lambda x: x.sit)
            ]
            ,
            'order':[
                p.sit for p in sorted((self.players.all()), key=lambda x: x.sit)
            ]
        }

        self.move_queue = queue
        self.move_index = 0
    
    move_queue = models.JSONField(default=dict)
    last_bet = models.JSONField(default=dict)
    available_commands = models.JSONField(default=list)
    
    
    def init_bets():
        return {bet_round:[] for bet_round in [1,2,3,4]}

    bets = models.JSONField(default=init_bets)
    pots = models.JSONField(default=dict)
    
    BIG_BLIND = 10
    def get_call_amount(self,player:Player):
        if not self.bets[str(self.table_state)]:
            return 0
        
        call_amount = ( 
            max((self.get_player_total_bets_in_round(p,self.table_state) for p in self.players.all())))
        return call_amount
    
    def get_min_raise_amount(self):
        if not self.bets[str(self.table_state)]:
            return self.BIG_BLIND*2
        min_raise_amount = 2 * max([bet[2] for bet in self.bets[str(self.table_state)] if bet[1]=='raise']+[0])
        return min_raise_amount
    
    def get_player_total_bets_in_round(self, player: Player, round: int) -> int:
        return max((bet[2] for bet in self.bets[str(round)] if bet[0]==player.sit), default=0)
    

    class TableState(models.IntegerChoices):
        ENDED = 0
        PREFLOP = 1
        FLOP = 2
        TURN = 3
        RIVER = 4

    table_state = models.IntegerField(choices=TableState.choices,default=TableState.ENDED)

    deck = models.JSONField(default=list)

    def default_cards():
        return {i:None for i in range(1,10)}
    cards = models.JSONField(default=default_cards)
    community_cards = models.JSONField(default=list)

    def __str__(self):
        return self.table_name
    
# Many to many example models
class Member(models.Model):
    name = models.CharField(max_length=100)
    sit = models.IntegerField()
    def __str__(self) -> str:
        return f'{self.name} sit: {self.sit}'

class Group(models.Model):
    name = models.CharField(default='group',max_length=100)
    members = models.ManyToManyField(
        Member,
        through='Membership',
        through_fields=('group', 'member'),
    )

class Membership(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    member = models.ForeignKey(Member, on_delete=models.CASCADE)