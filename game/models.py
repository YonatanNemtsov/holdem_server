from django.db import models
from django.contrib.auth.models import User
# Create your models here.



class GameTable(models.Model):
    table_name = models.CharField(max_length=100,default='table',unique=True)

    player1 = models.ForeignKey(
        User,
        related_name='p1',
        on_delete=models.CASCADE,
        null=True
    )

    player2 = models.ForeignKey(
        User,
        related_name='p2',
        on_delete=models.CASCADE,
        null=True
    )

    p1_status = models.BooleanField(default=0)
    p2_status = models.BooleanField(default=0)
    
    to_move = models.CharField(default='p1',max_length=100)
    log = models.JSONField(default=list)
    
    def __str__(self):
        return self.table_name

class GameLog(models.Model):
    table = models.CharField(default='1', max_length=100)
    p1_name = models.CharField(default='p1', max_length=100)
    p2_name = models.CharField(default='p2', max_length=100)
    log = models.JSONField(default=list)
    def __str__(self) -> str:
        return self.table