# Generated by Django 5.2.1 on 2025-05-22 02:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('research', '0004_remove_politician_research_po_positio_790abb_idx_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='researchresult',
            name='position',
            field=models.CharField(max_length=200),
        ),
    ]
