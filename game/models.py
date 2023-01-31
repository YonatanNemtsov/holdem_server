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
    
    to_move = models.CharField(default=1,max_length=100)
    moves_made = models.IntegerField(default=0)
    log = models.JSONField(default=list)
    winner = models.CharField(default='',max_length=100)
    pot = models.IntegerField(default=0)
    first_to_move = models.IntegerField(default=1)

    move_queue = models.JSONField(default=list)
    
    def make_queue(self):
        sits_occupied = [p.sit for p in self.players.all()]
        first = sits_occupied.index(self.first_to_move)
        self.to_move = first
        queue = sits_occupied[first:].copy() + sits_occupied[:first].copy()
        self.move_queue = queue

    TABLE_STATE_CHOICES = (
        (ENDED:='ENDED','ended'),
        (ONGOING:='ONGOING','ongoing'), 
    )

    table_state = models.CharField(choices=TABLE_STATE_CHOICES,default=ENDED,max_length=10)

    def default_cards():
        return {i:None for i in range(1,10)}
    cards = models.JSONField(default=default_cards)

    def deal_cards(self):
        sits_occupied = [p.sit for p in self.players.all()]
        self.cards = {sit:randint(1,13) for sit in sits_occupied}

    def __str__(self):
        return self.table_name

# Many to many example 
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
