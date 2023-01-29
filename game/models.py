from django.db import models
from django.contrib.auth.models import User
# Create your models here.


class Player (models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    sit = models.IntegerField()
    def __str__(self):
        return f'{self.sit} {self.user.username}'

class GameTable(models.Model):
    # need to rewrite more elegantly.
    table_name = models.CharField(max_length=100,default='table',unique=True)
    
    player1 = models.ForeignKey(
        User,
        related_name='p1',
        on_delete=models.CASCADE,
        blank = True,
        null = True,
        default = None
    )

    player2 = models.ForeignKey(
        User,
        related_name='p2',
        on_delete=models.CASCADE,
        blank = True,
        null = True,
        default = None
    )

    players = models.ManyToManyField(
        Player,
    )
    
    to_move = models.CharField(default='p1',max_length=100)
    moves_made = models.IntegerField(default=0)
    log = models.JSONField(default=list)
    winner = models.CharField(default='',max_length=100)
    
    card1 = models.IntegerField(default=0)
    card2 = models.IntegerField(default=0)
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
