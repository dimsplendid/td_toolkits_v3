# Generated by Django 3.1.1 on 2022-04-19 03:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('opticals', '0032_auto_20220419_1029'),
    ]

    operations = [
        migrations.AddField(
            model_name='opticalreference',
            name='voltage',
            field=models.FloatField(default=5.0),
        ),
    ]
