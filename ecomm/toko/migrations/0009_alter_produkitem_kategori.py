# Generated by Django 4.2 on 2023-05-30 05:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('toko', '0008_alter_alamatpengiriman_options_payment_order_payment'),
    ]

    operations = [
        migrations.AlterField(
            model_name='produkitem',
            name='kategori',
            field=models.CharField(choices=[('S', 'Shirt'), ('SW', 'Sport wear'), ('OW', 'Outwear'), ('SN', 'Sneaker'), ('D', 'Dress')], max_length=2),
        ),
    ]
