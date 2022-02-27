from django.db import models

from autoslug import AutoSlugField
from model_utils.models import TimeStampedModel


class ProductModelType(TimeStampedModel):
    name = models.CharField(
        'short name',
        max_length=255)
    slug = AutoSlugField(
        'Product Address',
        unique=True, always_update=False, populate_from='name')
 
    @classmethod
    def default(cls):
        return cls.objects.get_or_create(name='5905')[0]

    def __str__(self):
        return self.name

class Experiment(TimeStampedModel):
    name = models.CharField(
        'Experiment ID',
        max_length=255,
    )
    slug = AutoSlugField(
        'Experiment Address',
        unique=True, always_update=False, populate_from='name')
    
    desc = models.TextField(
        'description', blank=True)

class Condition(TimeStampedModel):
    name = models.CharField(
        'Conditions',
        max_length=255,
    )
    slug = AutoSlugField(
        'Condtions Address',
        unique=True, always_update=False, populate_from='name')
    desc = models.TextField(
        'description', blank=True)
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE)
    
    # TODO: experiment conditions


    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'experiment'], name='unique_condition')
        ]


class Sub(TimeStampedModel):
    name = models.CharField(
        'sub id',
        max_length=255,
        help_text="If you don't have ID like some simple test cell, using \
            project_name"
    )
    slug = AutoSlugField(
        'Sub Address',
        unique=True, always_update=False, populate_from='name')
    product_type = models.ForeignKey(
        'ProductModelType',
        on_delete=models.CASCADE, null=True, blank=True)
    condition = models.ForeignKey(
        'Condition', 
        on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.name

class Chip(TimeStampedModel):
    name = models.CharField(
        'chip id',
        max_length=255,
        help_text="If you don't have ID like some simple test cell, using \
            project_name + your spcific id"
    )
    slug = AutoSlugField(
        'Sub Address',
        unique=True, always_update=False, populate_from='name')
    short_name = models.CharField(
        'short id',
        max_length=255, blank=True)
    sub = models.ForeignKey(
        'Sub', 
        on_delete=models.CASCADE, null=True, blank=True)
    
    lc = models.ForeignKey(
        'materials.LiquidCrystal',
        on_delete=models.CASCADE, null=True, blank=True)
    pi = models.ForeignKey(
        'materials.Polyimide',
        on_delete=models.CASCADE, null=True, blank=True)
    seal = models.ForeignKey(
        'materials.Seal',
        on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.name

    