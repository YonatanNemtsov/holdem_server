# Generated by Django 4.1.4 on 2023-01-29 14:48

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0025_group_member_membership_group_members'),
    ]

    operations = [
        migrations.DeleteModel(
            name='GameLog',
        ),
    ]