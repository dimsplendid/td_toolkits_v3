# Generated by Django 3.1.1 on 2022-03-23 08:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('opticals', '0021_auto_20220321_1321'),
    ]

    operations = [
        migrations.AddField(
            model_name='opticalreference',
            name='w_capital_y',
            field=models.FloatField(default=0, verbose_name='WY'),
            preserve_default=False,
        ),
    ]