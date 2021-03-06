# Generated by Django 3.1.1 on 2022-03-09 05:15

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0007_auto_20220302_1515'),
        ('opticals', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='RDLCellGap',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('chip', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='rdl_cellgap', to='products.chip')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
