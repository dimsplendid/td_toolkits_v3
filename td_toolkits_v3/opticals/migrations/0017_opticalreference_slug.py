# Generated by Django 3.1.1 on 2022-03-16 08:50

import autoslug.fields
from django.db import migrations
import td_toolkits_v3.opticals.models


class Migration(migrations.Migration):

    dependencies = [
        ('opticals', '0016_auto_20220316_0736'),
    ]

    operations = [
        migrations.AddField(
            model_name='opticalreference',
            name='slug',
            field=autoslug.fields.AutoSlugField(default='test', editable=False, populate_from=td_toolkits_v3.opticals.models.OpticalReference.slug_gen, unique=True, verbose_name='opt ref addr'),
            preserve_default=False,
        ),
    ]