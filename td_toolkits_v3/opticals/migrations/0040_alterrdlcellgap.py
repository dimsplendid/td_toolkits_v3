# Generated by Django 3.2.13 on 2023-09-26 14:33

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0013_auto_20220318_1420'),
        ('opticals', '0039_backlightintensity_backlightunit'),
    ]

    operations = [
        migrations.CreateModel(
            name='AlterRdlCellGap',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('measure_point', models.SmallIntegerField()),
                ('cell_gap', models.FloatField()),
                ('chip', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.chip')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]