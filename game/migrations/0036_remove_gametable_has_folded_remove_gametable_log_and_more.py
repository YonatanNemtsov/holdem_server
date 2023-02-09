# Generated by Django 4.1.4 on 2023-02-07 13:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0035_gametable_move_index_alter_gametable_move_queue'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='gametable',
            name='has_folded',
        ),
        migrations.RemoveField(
            model_name='gametable',
            name='log',
        ),
        migrations.RemoveField(
            model_name='gametable',
            name='moves_made',
        ),
        migrations.RemoveField(
            model_name='gametable',
            name='pot',
        ),
        migrations.RemoveField(
            model_name='gametable',
            name='to_move',
        ),
        migrations.RemoveField(
            model_name='gametable',
            name='winner',
        ),
        migrations.AlterField(
            model_name='gametable',
            name='pots',
            field=models.JSONField(default=dict),
        ),
    ]
