# Generated by Django 3.1.1 on 2022-03-15 04:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('opticals', '0012_responsetimelog'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='responsetimelog',
            constraint=models.UniqueConstraint(fields=('chip', 'measure_point', 'voltage'), name='rt_unique'),
        ),
    ]