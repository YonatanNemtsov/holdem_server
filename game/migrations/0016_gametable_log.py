# Generated by Django 4.1.4 on 2023-01-16 10:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0015_alter_gametable_player1_alter_gametable_player2'),
    ]

    operations = [
        migrations.AddField(
            model_name='gametable',
            name='log',
            field=models.JSONField(default=list),
        ),
    ]
