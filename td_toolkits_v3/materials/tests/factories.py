from pathlib import Path

from django.template.defaultfilters import slugify


import factory
import factory.fuzzy


from ..models import (
    Vender,
    LiquidCrystal,
    Polyimide,
    Seal
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

class PolyimideFactory(factory.django.DjangoModelFactory):

    name = factory.fuzzy.FuzzyText()
    slug = factory.LazyAttribute(
        lambda obj: slugify(obj.name)
    )
    vender = factory.SubFactory(VenderFactory, name='INX')

    class Meta:
        model = Polyimide

class SealFactory(factory.django.DjangoModelFactory):

    name = factory.fuzzy.FuzzyText()
    slug = factory.LazyAttribute(
        lambda obj: slugify(obj.name)
    )
    vender = factory.SubFactory(VenderFactory, name='INX')

    class Meta:
        model = Seal

TEST_DIR = Path(__file__).resolve(strict=True).parent

MATERIAL_TEST_FILE_DIR = TEST_DIR / r'test_files/batch_upload_test.xlsx'
MATERIAL_TEST_NULL_FILE_DIR = TEST_DIR / r'test_files/batch_upload_test_null.xlsx'