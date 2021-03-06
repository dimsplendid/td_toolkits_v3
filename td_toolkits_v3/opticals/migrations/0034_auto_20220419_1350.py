# Generated by Django 3.1.1 on 2022-04-19 05:50

import autoslug.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('opticals', '0033_opticalreference_voltage'),
    ]

    operations = [
        migrations.AlterField(
            model_name='opticalreference',
            name='slug',
            field=autoslug.fields.AutoSlugField(editable=False, populate_from=['product_model_type__name', 'product_model_type__factory__name'], unique=True, verbose_name='opt ref addr'),
        ),
    ]
