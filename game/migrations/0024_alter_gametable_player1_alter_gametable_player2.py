# Generated by Django 4.1.4 on 2023-01-29 13:34

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('game', '0023_alter_gametable_player1_alter_gametable_player2'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gametable',
            name='player1',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='p1', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='gametable',
            name='player2',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='p2', to=settings.AUTH_USER_MODEL),
        ),
    ]