# Generated by Django 5.2.1 on 2025-05-23 03:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('research', '0006_politician_bio_politician_issues_politician_party'),
    ]

    operations = [
        migrations.AlterField(
            model_name='politician',
            name='issues',
            field=models.TextField(blank=True),
        ),
    ]
