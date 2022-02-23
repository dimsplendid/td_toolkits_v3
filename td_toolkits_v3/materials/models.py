from autoslug import AutoSlugField
from django.db import models

from model_utils.models import TimeStampedModel

class Vender(TimeStampedModel):
    name = models.CharField("Name of Vender", max_length=255)
    slug = AutoSlugField("Vender Adress")

class LiquidCrystal(TimeStampedModel):
    name = models.CharField("Name of Liquid Crystal", max_length=255)
    slug = AutoSlugField(
        "LC Address",
        unique=True, always_update=False, populate_from="name")
    
