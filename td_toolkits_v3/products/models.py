from django.db import models

from autoslug import AutoSlugField
from model_utils.models import TimeStampedModel


class ProductModelType(TimeStampedModel):
    name = models.CharField(
        'short name',
        max_length=255,
    )
    slug = AutoSlugField(
        'Product Address',
        unique=True, always_update=False, populate_from='name'
    )
 
    @classmethod
    def default(cls):
        return cls.objects.get_or_create(name='5905')[0]

    def __str__(self):
        return self.name

class Sub(TimeStampedModel):
    name = models.CharField(
        'sub id',
        max_length=255,
    )
    slug = AutoSlugField(
        'Sub Address',
        unique=True, always_update=False, populate_from='name'
    )
    product_type = models.ForeignKey(
        ProductModelType,
        on_delete=models.CASCADE, null=True, blank=True
    )

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
        unique=True, always_update=False, populate_from='name'
    )
    short_name = models.CharField(
        'short id',
        max_length=255
    )
    sub = models.ForeignKey(
        Sub, 
        on_delete=models.CASCADE, null=True, blank=True)

    product_type = models.ForeignKey(
        ProductModelType,
        on_delete=models.CASCADE, null=True, blank=True
    )

    def __str__(self):
        return self.name

    