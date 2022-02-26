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