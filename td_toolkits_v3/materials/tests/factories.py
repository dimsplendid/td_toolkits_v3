from django.template.defaultfilters import slugify


import factory
import factory.fuzzy


from ..models import (
    Vender,
    LiquidCrystal,
)

class VenderFactory(factory.django.DjangoModelFactory):
    name = factory.fuzzy.FuzzyText()
    slug = factory.LazyAttribute(
        lambda obj: slugify(obj.name)
    )

    class Meta:
        model = Vender

class LiquidCrystalFactory(factory.django.DjangoModelFactory):

    name = factory.fuzzy.FuzzyText()
    slug = factory.LazyAttribute(
        lambda obj: slugify(obj.name)
    )
    vender = factory.SubFactory(VenderFactory, name='INX')

    class Meta:
        model = LiquidCrystal