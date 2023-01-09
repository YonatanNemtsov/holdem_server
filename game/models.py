from django.db import models
from django.contrib.auth.models import User
# Create your models here.



class GameTable(models.Model):
    table_name = models.CharField(max_length=100,default='table',unique=True)

    player1 = models.ForeignKey(
        User,
        related_name='p1',
        on_delete=models.CASCADE,
    )

    player2 = models.ForeignKey(
        User,
        related_name='p2',
        on_delete=models.CASCADE,
    )

    moves_log = models.JSONField(default=dict)

    player1_cards = models.IntegerField()
    player2_cards = models.IntegerField()

    def __str__(self):
        return self.table_name


class JsonTest(models.Model):
    name = models.CharField(max_length=100, unique=True)
    data = models.JSONField(default=dict)
    def __str__(self) -> str:
        return self.name

class GameLog(models.Model):
    p1_name = models.CharField(default='p1', max_length=100)
    p2_name = models.CharField(default='p2', max_length=100)
    log = models.JSONField(default=list)
