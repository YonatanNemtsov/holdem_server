# Generated by Django 4.1.4 on 2023-01-31 21:02

from django.db import migrations, models
import game.models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0027_player_gametable_players'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='gametable',
            name='card1',
        ),
        migrations.RemoveField(
            model_name='gametable',
            name='card2',
        ),
        migrations.RemoveField(
            model_name='gametable',
            name='player1',
        ),
        migrations.RemoveField(
            model_name='gametable',
            name='player2',
        ),
        migrations.AddField(
            model_name='gametable',
            name='cards',
            field=models.JSONField(default=game.models.GameTable.default_cards),
        ),
        migrations.AddField(
            model_name='gametable',
            name='first_to_move',
            field=models.IntegerField(default=1),
        ),
        migrations.AddField(
            model_name='gametable',
            name='move_queue',
            field=models.JSONField(default=list),
        ),
        migrations.AddField(
            model_name='gametable',
            name='pot',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='gametable',
            name='table_state',
            field=models.CharField(choices=[('ENDED', 'ended'), ('ONGOING', 'ongoing')], default='ENDED', max_length=10),
        ),
        migrations.AddField(
            model_name='player',
            name='chips',
            field=models.IntegerField(default=100),
        ),
        migrations.AlterField(
            model_name='gametable',
            name='to_move',
            field=models.CharField(default=1, max_length=100),
        ),
    ]