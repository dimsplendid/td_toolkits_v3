# Generated by Django 3.1.1 on 2022-03-24 14:22

from django.db import migrations, models
import picklefield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('opticals', '0023_auto_20220323_0830'),
    ]

    operations = [
        migrations.AddField(
            model_name='opticalsfittingmodel',
            name='r2',
            field=models.JSONField(default={}),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='opticalsfittingmodel',
            name='voltage',
            field=picklefield.fields.PickledObjectField(default='', editable=False),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='opticalsfittingmodel',
            name='w_capital_y',
            field=picklefield.fields.PickledObjectField(default='', editable=False),
            preserve_default=False,
        ),
    ]