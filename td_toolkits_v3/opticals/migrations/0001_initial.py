# Generated by Django 3.1.1 on 2022-02-27 06:35

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('products', '0003_auto_20220227_1409'),
    ]

    operations = [
        migrations.CreateModel(
            name='AxometricsLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('measure_point', models.SmallIntegerField()),
                ('x_coord', models.FloatField()),
                ('y_coord', models.FloatField()),
                ('cell_gap', models.FloatField()),
                ('top_rubbing_direct', models.FloatField()),
                ('twist', models.FloatField()),
                ('top_pretilt', models.FloatField()),
                ('bottom_pretilt', models.FloatField()),
                ('rms', models.FloatField()),
                ('iteration', models.FloatField()),
                ('chip', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.chip')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]