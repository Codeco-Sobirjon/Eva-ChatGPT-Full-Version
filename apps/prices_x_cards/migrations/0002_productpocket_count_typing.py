# Generated by Django 5.1.7 on 2025-04-08 10:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('prices_x_cards', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='productpocket',
            name='count_typing',
            field=models.PositiveIntegerField(blank=True, default=1, null=True, verbose_name='Количество вводов'),
        ),
    ]
