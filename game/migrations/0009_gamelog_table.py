# Generated by Django 4.1.4 on 2023-01-09 12:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0008_remove_gametable_games_log'),
    ]

    operations = [
        migrations.AddField(
            model_name='gamelog',
            name='table',
            field=models.CharField(default='', max_length=100, unique=True),
        ),
    ]