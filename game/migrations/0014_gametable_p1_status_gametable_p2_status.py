# Generated by Django 4.1.4 on 2023-01-15 11:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0013_remove_gametable_moves_log_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='gametable',
            name='p1_status',
            field=models.BooleanField(default=0),
        ),
        migrations.AddField(
            model_name='gametable',
            name='p2_status',
            field=models.BooleanField(default=0),
        ),
    ]
