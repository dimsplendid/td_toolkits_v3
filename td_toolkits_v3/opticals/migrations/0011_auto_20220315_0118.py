# Generated by Django 3.1.1 on 2022-03-15 01:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('opticals', '0010_auto_20220311_1554'),
    ]

    operations = [
        migrations.AlterField(
            model_name='opticallog',
            name='voltage',
            field=models.FloatField(verbose_name='Vop'),
        ),
    ]
