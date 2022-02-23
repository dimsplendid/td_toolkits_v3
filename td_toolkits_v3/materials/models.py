from django.db import models

from autoslug import AutoSlugField
from model_utils.models import TimeStampedModel


class Vender(TimeStampedModel):
    name = models.CharField("Name of Vender", max_length=255)
    slug = AutoSlugField(
        "Vender Adress",
        unique=True, always_update=False, populate_from="name")

    def __str__(self):
        return self.name


def get_default_vender():
    return Vender.objects.get_or_create(name="INX")[0]


class LiquidCrystal(TimeStampedModel):
    name = models.CharField("Name of Liquid Crystal", max_length=255)
    slug = AutoSlugField(
        "LC Address",
        unique=True, always_update=False, populate_from="name")
    vender = models.ForeignKey(
        Vender,
        default=get_default_vender, on_delete=models.CASCADE)

    def __str__(self):
        return self.name
