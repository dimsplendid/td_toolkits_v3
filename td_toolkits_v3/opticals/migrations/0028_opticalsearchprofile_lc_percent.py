# Generated by Django 3.1.1 on 2022-03-27 18:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('opticals', '0027_auto_20220327_1848'),
    ]

    operations = [
        migrations.AddField(
            model_name='opticalsearchprofile',
            name='lc_percent',
            field=models.FloatField(default=0.0, verbose_name='LC%'),
        ),
    ]