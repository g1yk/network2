# Generated by Django 3.2.6 on 2021-11-30 01:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('network', '0017_auto_20211130_0150'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='like',
            name='total_likes',
        ),
    ]
