from django.db import models
from django.contrib.auth.models import User

from random import randint
# Create your models here.

class UserAccount(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.IntegerField(default=1000)
    chips_in_action = models.IntegerField(default=0)

class GameTable(models.Model):
    def default_config(): 
        return {
            'small_blind': 20,
            'ante': 0,
            'min_buyin': 100,
            'max_buyin': 500,
            'num_of_sits': 9,
        }
    table_name = models.CharField(max_length=100, default='table')
    config = models.JSONField(
        default = default_config
    )
    