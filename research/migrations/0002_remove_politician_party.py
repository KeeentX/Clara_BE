# Generated by Django 5.2.1 on 2025-05-19 13:10

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('research', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='politician',
            name='party',
        ),
    ]
