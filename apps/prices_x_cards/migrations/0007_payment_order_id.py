# Generated by Django 5.1.7 on 2025-04-25 16:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('prices_x_cards', '0006_alter_productpocket_options_delete_tobuyeruser'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='order_id',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Номер заказа'),
        ),
    ]
