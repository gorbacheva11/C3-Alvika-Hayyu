# Generated by Django 4.2 on 2023-05-31 11:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('toko', '0014_delete_kontak'),
    ]

    operations = [
        migrations.AlterField(
            model_name='produkitem',
            name='kategori',
            field=models.CharField(choices=[('all', 'all'), ('S', 'Shirt'), ('SW', 'Sport wear'), ('OW', 'Outwear'), ('A', 'Accesories'), ('D', 'Dress')], max_length=3),
        ),
    ]