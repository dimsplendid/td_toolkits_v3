from django.db import models
from autoslug import AutoSlugField
from model_utils.models import TimeStampedModel

class Project(TimeStampedModel):
    name = models.CharField(max_length=255)
    fab = models.ForeignKey(
        to='products.Factory',
        on_delete=models.CASCADE,
    )