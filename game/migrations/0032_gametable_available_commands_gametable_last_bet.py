# Generated by Django 4.1.4 on 2023-02-02 13:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0031_alter_gametable_table_state'),
    ]

    operations = [
        migrations.AddField(
            model_name='gametable',
            name='available_commands',
            field=models.JSONField(default=list),
        ),
        migrations.AddField(
            model_name='gametable',
            name='last_bet',
            field=models.JSONField(default=dict),
        ),
    ]